import pytest
from fastapi.testclient import TestClient

from app import main
from app.qloo_adapter import QlooAdapter, QlooAuthError


@pytest.fixture
def client():
    main.reset_state()
    return TestClient(main.app)


def demo(client):
    return client.get("/api/presets").json()["demo_profile"]


def new_session(client):
    r = client.post("/api/session", json=demo(client))
    assert r.status_code == 200, r.text
    return r.json()["session_id"]


def test_health(client):
    body = client.get("/api/health").json()
    assert body["status"] == "ok" and body["qloo_mode"] == "mock" and body["llm_mode"] == "off"
    assert "qloo_calls_used" in body and body["version"]


def test_presets(client):
    body = client.get("/api/presets").json()
    assert body["demo_profile"]["destination_city"] == "Toronto"
    assert "food" in body["preserve_chips"]


def test_session_resolver_summary(client):
    r = client.post("/api/session", json=demo(client)).json()
    assert len(r["resolver"]["resolved"]) >= 3
    assert {u["input"] for u in r["resolver"]["unresolved"]} == {"Lahore street food", "chai with friends"}


def test_validation_errors_are_readable(client):
    bad = demo(client) | {"budget_per_activity_cad": 999, "loved_items": [{"text": "x" * 200, "type": "dish"}]}
    r = client.post("/api/session", json=bad)
    assert r.status_code == 422
    msg = r.json()["error"]["message"]
    assert "budget_per_activity_cad" in msg and "80 characters" in msg
    assert client.post("/api/session", json=demo(client) | {"destination_city": "Paris"}).status_code == 422
    assert client.post("/api/feedback", json={"session_id": "x", "action": "explode"}).status_code == 422


def test_bridge_plan_feedback_familiarity(client):
    sid = new_session(client)
    bridge = client.post("/api/bridge", json={"session_id": sid}).json()
    assert set(bridge["categories"]) >= {"food", "music", "social"}
    food = bridge["categories"]["food"]
    assert food["familiar"] and food["discover"]

    plan = client.post("/api/plan", json={"session_id": sid}).json()["plan"]
    assert plan["items"] and all(i["candidate"]["source"] in ("qloo", "curated", "unverified") for i in plan["items"])
    assert all(i["explanation_source"] == "template" for i in plan["items"])

    low = client.post("/api/familiarity", json={"session_id": sid, "value": 0}).json()
    high = client.post("/api/familiarity", json={"session_id": sid, "value": 1}).json()
    assert low["familiarity"] == 0 and high["familiarity"] == 1
    assert any(low["categories"][c]["top_ids"] != high["categories"][c]["top_ids"] for c in low["categories"])

    fb = client.post("/api/feedback", json={"session_id": sid, "action": "more_familiar"}).json()
    assert fb["changes"] and fb["profile"]["familiarity"] == 1.0


def test_expired_session(client):
    for path in ("/api/bridge", "/api/plan"):
        r = client.post(path, json={"session_id": "nope"})
        assert r.status_code == 404 and r.json()["error"]["code"] == "session_not_found"
    assert client.get("/api/compare/nope").status_code == 404


def test_session_ttl_expiry(client):
    clock = [0.0]
    main.state.store.clock = lambda: clock[0]
    sid = new_session(client)
    clock[0] = 2 * 3600 + 1
    assert client.post("/api/plan", json={"session_id": sid}).status_code == 404


def test_reset_session(client):
    sid = new_session(client)
    assert client.delete(f"/api/session/{sid}").json()["deleted"] is True
    assert client.post("/api/plan", json={"session_id": sid}).status_code == 404


def test_missing_llm_key_falls_back_to_template(client, monkeypatch):
    monkeypatch.setenv("LLM_MODE", "on")
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    sid = new_session(client)
    assert client.get("/api/health").json()["llm_mode"] == "off"
    items = client.post("/api/plan", json={"session_id": sid}).json()["plan"]["items"]
    assert all(i["explanation_source"] == "template" for i in items)
    assert items[0]["why_this"]
    baseline = client.get(f"/api/compare/{sid}").json()["baseline"]
    assert baseline["available"] is False and "unavailable" in baseline["message"].lower()


def test_qloo_failure_is_structured(client, monkeypatch):
    async def boom(*a, **k):
        raise QlooAuthError("secret detail")
    main.state.adapter = QlooAdapter(mode="mock")
    monkeypatch.setattr(main.state.adapter, "search_entities", boom)
    r = client.post("/api/session", json=demo(client))
    assert r.status_code == 502
    err = r.json()["error"]
    assert err["code"] == "qloo_auth" and "secret detail" not in r.text


def test_admin_cohort(client):
    body = client.get("/api/admin/cohort").json()
    assert body["label"] == "Synthetic demo data" and body["clusters"]


def test_unknown_api_route(client):
    assert client.get("/api/nope").status_code == 404

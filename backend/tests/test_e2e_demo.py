"""Demo scenario, mock mode: session -> bridge -> plan -> "too expensive" -> compare."""

from fastapi.testclient import TestClient

from app import main


def test_demo_path():
    main.reset_state()
    c = TestClient(main.app)
    profile = c.get("/api/presets").json()["demo_profile"]
    assert profile["origin"] == "Pakistan"

    session = c.post("/api/session", json=profile).json()
    sid = session["session_id"]
    assert len(session["resolver"]["resolved"]) >= 3
    assert session["resolver"]["unresolved"]

    bridge = c.post("/api/bridge", json={"session_id": sid}).json()
    for cat in bridge["categories"].values():
        for card in cat["familiar"] + cat["discover"]:
            ev = card["candidate"]["evidence"]
            assert card["candidate"]["source"] in ("qloo", "curated", "unverified")
            if card["candidate"]["source"] == "qloo":
                assert ev["seed_inputs"] and ev["qloo_entity"] and ev["qloo_signal"] and ev["city_signal"]

    plan = c.post("/api/plan", json={"session_id": sid}).json()["plan"]
    items = plan["items"]
    assert {i["day"] for i in items} <= set(range(1, 8))
    assert any(i["candidate"]["social"] for i in items)
    assert any(i["candidate"]["source"] == "qloo" for i in items)

    target = items[0]["candidate"]["id"]
    fb = c.post("/api/feedback", json={"session_id": sid, "action": "too_expensive", "item_id": target}).json()
    new_items = fb["plan"]["items"]
    assert [(i["day"], i["candidate"]["id"]) for i in new_items] != [(i["day"], i["candidate"]["id"]) for i in items]
    assert target not in {i["candidate"]["id"] for i in new_items}
    assert fb["changes"] and fb["profile"]["budget_per_activity_cad"] == 14
    assert all(i["candidate"]["source"] in ("qloo", "curated", "unverified") for i in new_items)

    compare = c.get(f"/api/compare/{sid}").json()
    assert compare["baseline"]["available"] is False  # LLM off in tests: no fake baseline
    assert all(i["candidate"]["source"] for i in compare["tastebridge"])
    assert c.get("/api/health").json()["qloo_calls_used"] == 0  # mock mode never runs the CLI

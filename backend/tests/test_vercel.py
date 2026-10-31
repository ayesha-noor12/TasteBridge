"""HTTP transport for Qloo and the Redis session store (used on Vercel), with mocked HTTP."""

import asyncio
import json

import httpx
import pytest

from app import qloo_adapter, sessions
from app.qloo_adapter import QlooAdapter, QlooAuthError, QlooRateLimitError, http_runner
from tests.helpers import cand, profile


def run(coro):
    return asyncio.run(coro)


REAL_CLIENT = httpx.AsyncClient


def mock_http(monkeypatch, module, handler):
    monkeypatch.setattr(module.httpx, "AsyncClient", lambda **kw: REAL_CLIENT(transport=httpx.MockTransport(handler), **kw))


@pytest.fixture
def qloo_env(monkeypatch):
    monkeypatch.setenv("QLOO_API_KEY", "secret-key")
    monkeypatch.delenv("QLOO_BASE_URL", raising=False)
    monkeypatch.delenv("QLOO_TRUSTED_BASE_URL", raising=False)


def test_http_search_sends_cli_request_and_prints_cli_json(monkeypatch, qloo_env):
    seen = []

    def handler(req):
        seen.append(req)
        return httpx.Response(200, json={"results": [{"entity_id": "E1", "name": "Coke Studio"}]})

    mock_http(monkeypatch, qloo_adapter, handler)
    rc, out, _ = run(http_runner(["qloo", "api", "search", "--query=a=b", "--type=artist", "--take=3", "--json"], 5))
    assert rc == 0 and json.loads(out) == [{"entity_id": "E1", "name": "Coke Studio"}]
    req = seen[0]
    assert str(req.url).startswith("https://api.qloo.com/search?")
    assert dict(req.url.params) == {"query": "a=b", "take": "3", "types": "urn:entity:artist"}
    assert req.headers["X-Api-Key"] == "secret-key"


def test_http_insights_unwraps_entities(monkeypatch, qloo_env):
    seen = []

    def handler(req):
        seen.append(req)
        return httpx.Response(200, json={"results": {"entities": [{"entity_id": "P1", "name": "Place"}]}})

    mock_http(monkeypatch, qloo_adapter, handler)
    argv = ["qloo", "api", "insights", "--type=place", "--signal-entities=A1,B2", "--filter-location=Toronto", "--take=10", "--json"]
    rc, out, _ = run(http_runner(argv, 5))
    assert rc == 0 and json.loads(out)[0]["entity_id"] == "P1"
    assert seen[0].url.path == "/v2/insights"
    assert dict(seen[0].url.params) == {
        "filter.type": "urn:entity:place",
        "signal.interests.entities": "A1,B2",
        "take": "10",
        "filter.location.query": "Toronto",
    }


def test_http_key_only_sent_to_trusted_base_url(monkeypatch, qloo_env):
    mock_http(monkeypatch, qloo_adapter, lambda req: pytest.fail("request must not be sent"))
    monkeypatch.setenv("QLOO_BASE_URL", "https://evil.example.com")
    rc, _, _ = run(http_runner(["qloo", "api", "search", "--query=x", "--take=1", "--json"], 5))
    assert rc == qloo_adapter.EXIT_AUTH

    monkeypatch.setenv("QLOO_TRUSTED_BASE_URL", "https://evil.example.com/")
    mock_http(monkeypatch, qloo_adapter, lambda req: httpx.Response(200, json={"results": []}))
    rc, _, _ = run(http_runner(["qloo", "api", "search", "--query=x", "--take=1", "--json"], 5))
    assert rc == 0


@pytest.mark.parametrize("status,exc", [(401, QlooAuthError), (429, QlooRateLimitError)])
def test_http_errors_map_through_adapter(monkeypatch, qloo_env, tmp_path, status, exc):
    mock_http(monkeypatch, qloo_adapter, lambda req: httpx.Response(status, json={"message": "nope"}))
    adapter = QlooAdapter(mode="live", cache_dir=tmp_path, runner=http_runner)
    with pytest.raises(exc):
        run(adapter.search_entities("x", None, 3))


def test_http_timeout_is_retried_once(monkeypatch, qloo_env, tmp_path):
    calls = []

    def handler(req):
        calls.append(req)
        raise httpx.ReadTimeout("slow", request=req)

    mock_http(monkeypatch, qloo_adapter, handler)
    adapter = QlooAdapter(mode="live", cache_dir=tmp_path, runner=http_runner)
    with pytest.raises(qloo_adapter.QlooUnavailable):
        run(adapter.search_entities("x", None, 3))
    assert len(calls) == 2


def test_vercel_defaults(monkeypatch):
    from app import config

    monkeypatch.delenv("CACHE_DIR", raising=False)
    monkeypatch.delenv("QLOO_TRANSPORT", raising=False)
    monkeypatch.setenv("VERCEL", "1")
    assert config.qloo_transport() == "http"
    assert str(config.cache_dir()).startswith("/tmp/")
    assert QlooAdapter(mode="live").runner is http_runner


def test_redis_store_round_trip(monkeypatch):
    db = {}

    def handler(req):
        assert req.headers["Authorization"] == "Bearer tok"
        cmd, key, *rest = json.loads(req.content)
        if cmd == "SET":
            db[key] = rest[0]
            return httpx.Response(200, json={"result": "OK"})
        if cmd == "GETEX":
            return httpx.Response(200, json={"result": db.get(key)})
        if cmd == "DEL":
            return httpx.Response(200, json={"result": int(db.pop(key, None) is not None)})
        raise AssertionError(cmd)

    mock_http(monkeypatch, sessions, handler)
    monkeypatch.setenv("KV_REST_API_URL", "https://redis.example.com")
    monkeypatch.setenv("KV_REST_API_TOKEN", "tok")
    store = sessions.make_store()
    assert isinstance(store, sessions.RedisSessionStore)

    from app.models import ResolverSummary

    s = sessions.Session(profile=profile(), resolver=ResolverSummary(resolved=[], unresolved=[]),
                         candidates=[cand("c1", source="qloo")], qloo_notes=["n"], rejected_ids={"x"})
    sid = run(store.create(s))
    got = run(store.get(sid))
    assert got.qloo_notes == ["n"] and got.rejected_ids == {"x"}
    assert got.candidates[0].id == "c1" and got.profile.origin == "Pakistan"
    got.min_social = 3
    run(store.save(sid, got))
    assert run(store.get(sid)).min_social == 3
    assert run(store.delete(sid)) is True
    assert run(store.get(sid)) is None

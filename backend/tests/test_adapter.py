import asyncio
import inspect
import json
import logging

import pytest

from app import qloo_adapter
from app.qloo_adapter import (
    QlooAdapter,
    QlooAuthError,
    QlooNoResult,
    QlooRateLimitError,
    QlooUnavailable,
    build_insights_argv,
    build_search_argv,
)

ONE_ENTITY = json.dumps([{"entity_id": "E1", "name": "Coke Studio", "type": "urn:entity:artist"}])


class FakeRunner:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    async def __call__(self, argv, timeout):
        self.calls.append(argv)
        r = self.responses.pop(0)
        if isinstance(r, BaseException):
            raise r
        return r


def live(tmp_path, runner):
    return QlooAdapter(mode="live", binary="qloo", cache_dir=tmp_path, runner=runner)


def run(coro):
    return asyncio.run(coro)


def test_search_argv():
    assert build_search_argv("qloo", "Coke Studio", "artist", 3) == [
        "qloo", "api", "search", "--query=Coke Studio", "--type=artist", "--take=3", "--json",
    ]


def test_search_argv_user_text_never_becomes_a_flag():
    argv = build_search_argv("qloo", "--api-key=steal; rm -rf /", None, 3)
    assert argv[3] == "--query=--api-key=steal; rm -rf /"
    assert not any(a.startswith("--api-key") for a in argv)


def test_insights_argv():
    assert build_insights_argv("qloo", ["A1", "B2"], "place", "Toronto", 10) == [
        "qloo", "api", "insights", "--type=place", "--signal-entities=A1,B2",
        "--filter-location=Toronto", "--take=10", "--json",
    ]


def test_argv_whitelist():
    with pytest.raises(ValueError):
        build_search_argv("qloo", "x", "rm -rf", 3)
    with pytest.raises(ValueError):
        build_insights_argv("qloo", ["bad id;"], "place", None, 3)


def test_no_shell_true_anywhere():
    src = inspect.getsource(qloo_adapter)
    assert "shell=True" not in src
    assert "create_subprocess_shell" not in src
    assert "create_subprocess_exec" in src


def test_search_parses_and_counts(tmp_path):
    runner = FakeRunner([(0, ONE_ENTITY, "")])
    adapter = live(tmp_path, runner)
    result = run(adapter.search_entities("Coke Studio", "artist", 3))
    assert [e.entity_id for e in result] == ["E1"]
    assert adapter.calls_used == 1


def test_timeout_then_one_retry_succeeds(tmp_path):
    runner = FakeRunner([asyncio.TimeoutError(), (0, ONE_ENTITY, "")])
    adapter = live(tmp_path, runner)
    assert len(run(adapter.search_entities("x", None, 3))) == 1
    assert len(runner.calls) == 2


def test_two_timeouts_raise_unavailable(tmp_path):
    runner = FakeRunner([asyncio.TimeoutError(), asyncio.TimeoutError(), (0, ONE_ENTITY, "")])
    with pytest.raises(QlooUnavailable):
        run(live(tmp_path, runner).search_entities("x", None, 3))
    assert len(runner.calls) == 2  # max 1 retry


def test_no_retry_on_non_timeout_error(tmp_path):
    runner = FakeRunner([(5, '{"error":true,"code":"API_ERROR","message":"API request failed: 500"}', ""), (0, ONE_ENTITY, "")])
    with pytest.raises(QlooUnavailable):
        run(live(tmp_path, runner).search_entities("x", None, 3))
    assert len(runner.calls) == 1


def test_cache_hit_avoids_second_subprocess(tmp_path):
    runner = FakeRunner([(0, ONE_ENTITY, "")])
    adapter = live(tmp_path, runner)
    run(adapter.search_entities("Coke Studio", "artist", 3))
    run(adapter.search_entities("Coke Studio", "artist", 3))
    assert len(runner.calls) == 1
    assert adapter.cache_hits == 1


@pytest.mark.parametrize(
    "rc,out,exc",
    [
        (3, '{"error":true,"code":"AUTH_FAILED","message":"No API key found."}', QlooAuthError),
        (5, '{"error":true,"code":"API_ERROR","message":"API request failed: 401 Unauthorized"}', QlooAuthError),
        (5, '{"error":true,"code":"API_ERROR","message":"API request failed: 429 Too Many Requests"}', QlooRateLimitError),
        (4, '{"error":true,"code":"NOT_FOUND","message":"Entity not found."}', QlooNoResult),
        (0, "this is not json", QlooUnavailable),
    ],
)
def test_errors_map_to_typed_exceptions(tmp_path, rc, out, exc):
    with pytest.raises(exc):
        run(live(tmp_path, FakeRunner([(rc, out, "")])).search_entities("x", None, 3))


def test_missing_binary_is_unavailable(tmp_path):
    with pytest.raises(QlooUnavailable):
        run(live(tmp_path, FakeRunner([FileNotFoundError()])).search_entities("x", None, 3))


def test_credential_never_in_exceptions_or_logs(tmp_path, monkeypatch, caplog):
    secret = "sk-very-secret-qloo-key"
    monkeypatch.setenv("QLOO_API_KEY", secret)
    out = f'{{"error":true,"code":"API_ERROR","message":"API request failed: 401 key {secret}"}}'
    runner = FakeRunner([asyncio.TimeoutError(), (5, out, f"stderr {secret}")])
    caplog.set_level(logging.DEBUG)
    with pytest.raises(QlooAuthError) as info:
        run(live(tmp_path, runner).search_entities("x", None, 3))
    assert secret not in str(info.value)
    assert secret not in info.value.detail
    assert secret not in caplog.text
    assert not any(secret in a for call in runner.calls for a in call)


def test_mock_mode_loads_fixtures():
    adapter = QlooAdapter(mode="mock")
    found = run(adapter.search_entities("Coke Studio", "artist", 3))
    assert found and "DEMO" in found[0].name
    assert run(adapter.search_entities("Lahore street food", "place", 3)) == []
    recs = run(adapter.recommend(["x"], "place", "Toronto", 10))
    assert recs[0].rank == 1 and recs[0].affinity is not None
    assert adapter.calls_used == 0


def test_mock_fixture_is_labeled_synthetic():
    data = json.loads((qloo_adapter.config.FIXTURES_DIR / "qloo_mock.json").read_text())
    assert "DEMO DATA, not from Qloo" in data["_notice"]


def test_parse_results_reads_nested_affinity_and_bad_items():
    payload = {"results": {"entities": [
        {"entity_id": "A", "name": "One", "query": {"affinity": 0.8}},
        {"name": "missing id"},
        "garbage",
    ]}}
    results = qloo_adapter.parse_results(payload)
    assert [(r.entity_id, r.affinity, r.rank, r.total) for r in results] == [("A", 0.8, 1, 1)]


def test_image_url_only_from_qloo_image_host():
    good = {"entity_id": "a", "name": "A", "properties": {"image": {"url": "https://images.qloo.com/i/a.jpg"}}}
    bad = {"entity_id": "b", "name": "B", "properties": {"image": {"url": "https://evil.example/x.jpg"}}}
    assert [r.image_url for r in qloo_adapter.parse_results([good, bad])] == ["https://images.qloo.com/i/a.jpg", None]
    assert qloo_adapter.parse_entities([good])[0].image_url == "https://images.qloo.com/i/a.jpg"

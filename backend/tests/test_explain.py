import asyncio
import json
from types import SimpleNamespace

from app import explain
from tests.helpers import cand, profile


class FakeLLM:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = 0
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    async def create(self, **kw):
        self.calls += 1
        assert "Use ONLY the JSON evidence" in kw["messages"][0]["content"]
        msg = SimpleNamespace(content=self.replies.pop(0))
        return SimpleNamespace(choices=[SimpleNamespace(message=msg)])


GOOD = json.dumps({"why_this": "Qloo linked it to Coke Studio.", "why_here": "Toronto result.", "why_now": "Start gently."})


def run(c, client, monkeypatch):
    monkeypatch.setenv("LLM_MODE", "on")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    return asyncio.run(explain.explain(c, profile(), "hint", client))


def test_llm_valid_json_is_used(monkeypatch):
    exp, src = run(cand("q", source="qloo", rank=1, total=2), FakeLLM([GOOD]), monkeypatch)
    assert src == "ai" and exp.why_this.startswith("Qloo linked")


def test_parse_failure_retries_once_then_template(monkeypatch):
    llm = FakeLLM(["not json", '{"why_this": "x"}', GOOD])
    exp, src = run(cand("q", source="qloo", rank=1, total=2), llm, monkeypatch)
    assert src == "template" and llm.calls == 2
    assert exp.why_this.startswith("Matches your interest in x; Qloo returned q for Toronto.")


def test_llm_may_not_add_urls_or_prices(monkeypatch):
    bad = json.dumps({"why_this": "See https://example.com", "why_here": "Only $5", "why_now": "now"})
    exp, src = run(cand("c"), FakeLLM([bad, bad]), monkeypatch)
    assert src == "template"


def test_template_marks_unknowns():
    exp = explain.template(cand("u", source="unverified"), profile(), "now")
    assert "Not a Qloo match" in exp.why_this
    assert "cost not verified" in exp.why_here and "travel time not verified" in exp.why_here


def test_json_wrapped_in_prose_is_accepted(monkeypatch):
    reply = "Here you go:\n```json\n" + GOOD + "\n```\nHope that helps."
    exp, src = run(cand("q", source="qloo", rank=1, total=2), FakeLLM([reply]), monkeypatch)
    assert src == "ai"


class FailingLLM:
    def __init__(self, exc):
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))
        self.exc = exc

    async def create(self, **kw):
        raise self.exc


def test_baseline_failure_says_why_without_key(monkeypatch):
    import httpx
    import openai

    from app.baseline import run_baseline

    monkeypatch.setenv("LLM_MODE", "on")
    monkeypatch.setenv("LLM_API_KEY", "sk-secret-123")
    err = openai.APIConnectionError(request=httpx.Request("POST", "https://x.invalid/v1"))
    res = asyncio.run(run_baseline(profile(), FailingLLM(err)))
    assert not res.available and "LLM_BASE_URL" in res.message and "sk-secret" not in res.message


def test_baseline_parses_list_after_prose(monkeypatch):
    from app.baseline import run_baseline

    monkeypatch.setenv("LLM_MODE", "on")
    monkeypatch.setenv("LLM_API_KEY", "k")
    reply = 'Sure! [{"name": "A", "description": "d"}, {"name": "B"}]'

    async def create(**kw):
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=reply))])

    llm = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    res = asyncio.run(run_baseline(profile(), llm))
    assert [s.name for s in res.suggestions] == ["A", "B"]

import asyncio

from app.models import LovedItem
from app.qloo_adapter import QlooAdapter
from app.resolver import resolve
from app import resolver


def run(items):
    return asyncio.run(resolve(QlooAdapter(mode="mock"), items))


def test_resolved_vs_unresolved_split():
    s = run([LovedItem(text="Coke Studio", type="artist"), LovedItem(text="Biryani", type="dish"),
             LovedItem(text="Nusrat Fateh Ali Khan", type="artist"), LovedItem(text="Lahore street food", type="dish")])
    assert [r.input for r in s.resolved] == ["Coke Studio", "Biryani", "Nusrat Fateh Ali Khan"]
    assert [u.input for u in s.unresolved] == ["Lahore street food"]
    assert "no matching entity" in s.unresolved[0].reason


def test_empty_input():
    assert run([]).resolved == []
    s = run([LovedItem(text="   ", type="dish")])
    assert s.unresolved[0].reason == "empty input"


def test_unsafe_characters_handled():
    item = LovedItem(text="Coke\x00 Studio\n", type="artist")
    assert item.text == "Coke Studio"
    s = run([item, LovedItem(text="--api-key=x; rm -rf / $(whoami)", type="activity")])
    assert len(s.resolved) == 1 and len(s.unresolved) == 1


def test_too_long_is_rejected():
    import pytest
    with pytest.raises(ValueError):
        LovedItem(text="a" * 81, type="dish")


def test_search_type_mapping_uses_whitelisted_types():
    from app.qloo_adapter import ALLOWED_TYPES
    assert all(t is None or t in ALLOWED_TYPES for t in resolver.SEARCH_TYPE.values())

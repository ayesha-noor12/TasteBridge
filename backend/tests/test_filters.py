from app import filters
from tests.helpers import cand, profile


def test_budget():
    kept, dropped = filters.apply([cand("a", cost=10), cand("b", cost=30)], profile(budget_per_activity_cad=20))
    assert [c.id for c in kept] == ["a"] and "budget" in dropped[0].reason


def test_travel():
    kept, _ = filters.apply([cand("a", travel=30), cand("b", travel=60)], profile(max_travel_minutes=40))
    assert [c.id for c in kept] == ["a"]


def test_diet():
    p = profile(diet=["halal"])
    kept, dropped = filters.apply(
        [cand("tagged", diet=["halal"]), cand("other", diet=["vegetarian"]), cand("unknown"),
         cand("music", category="music")], p)
    assert {c.id for c in kept} == {"tagged", "unknown", "music"}
    assert dropped[0].name == "other"
    assert filters.FLAG_DIET in next(c for c in kept if c.id == "unknown").flags


def test_comfort_prefer_friend_excludes_solo_only():
    kept, _ = filters.apply([cand("solo", solo_only=True), cand("group")], profile(comfort="prefer_friend"))
    assert [c.id for c in kept] == ["group"]
    kept, _ = filters.apply([cand("solo", solo_only=True)], profile(comfort="solo_ok"))
    assert len(kept) == 1


def test_unknown_fields_kept_and_flagged():
    kept, dropped = filters.apply([cand("u", source="unverified")], profile())
    assert not dropped
    assert {filters.FLAG_COST, filters.FLAG_TRAVEL, filters.FLAG_SOURCE} <= set(kept[0].flags)
    assert filters.is_unverified(kept[0])


def test_rejected_ids_dropped():
    kept, dropped = filters.apply([cand("a", cost=5)], profile(), {"a"})
    assert not kept and dropped

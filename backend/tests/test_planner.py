from collections import Counter

from app import planner, ranker
from tests.helpers import cand, profile


def pool():
    out = []
    for i in range(6):
        out.append(cand(f"qf{i}", category="food", mode="familiar" if i < 3 else "discover", source="qloo", rank=i + 1, total=6))
    for i in range(4):
        out.append(cand(f"qm{i}", category="music", mode="familiar" if i < 2 else "discover", source="qloo", rank=i + 1, total=4))
    for i in range(4):
        out.append(cand(f"s{i}", category="social", mode="discover", social=True, recurring=True, source="unverified"))
    out.append(cand("act", category="activity", mode="discover", source="unverified"))
    return out


def plan(**kw):
    p = profile(**kw)
    return planner.build(ranker.rank(pool(), p), p.hours_per_week, 1, p.familiarity)[0]


def test_seven_days_and_limits():
    items = plan(hours_per_week=40)
    days = Counter(s.day for s in items)
    assert set(days) <= set(range(1, 8)) and set(range(1, 8)) <= set(days)
    assert max(days.values()) <= 2
    assert len({s.candidate.id for s in items}) == len(items)
    assert len({(s.day, s.slot) for s in items}) == len(items)


def test_guarantees():
    for fam in (0.0, 0.5, 1.0):
        items = plan(familiarity=fam, hours_per_week=6)
        assert any(s.candidate.social for s in items)
        assert any(s.candidate.mode == "familiar" for s in items)
        assert any(s.candidate.mode == "discover" for s in items)


def test_familiar_anchor_first_social_later():
    items = plan()
    assert items[0].candidate.mode == "familiar" and items[0].day == 1
    social_days = [s.day for s in items if s.candidate.social]
    assert min(social_days) > 1


def test_respects_hours_per_week():
    for hours in (1, 2, 5, 12, 40):
        items = plan(hours_per_week=hours)
        assert sum(planner.item_hours(s.candidate) for s in items) <= hours
    assert len(plan(hours_per_week=1)) == 1  # unknown durations count as config.DEFAULT_ITEM_HOURS (1 h)


def test_familiar_share_follows_slider():
    share = []
    for fam in (0.0, 0.5, 1.0):
        items = plan(familiarity=fam, hours_per_week=16)
        share.append(sum(s.candidate.mode == "familiar" for s in items) / len(items))
    assert share[0] < share[1] < share[2]


def test_anchor_prefers_familiar_food():
    items = plan()
    assert items[0].candidate.category == "food" and items[0].candidate.mode == "familiar"

import asyncio

import pytest

from app import candidates, config, feedback, pipeline, resolver
from app.models import LovedItem
from app.qloo_adapter import QlooAdapter
from app.sessions import Session
from tests.helpers import profile

LOVED = [LovedItem(text="Coke Studio", type="artist"), LovedItem(text="Biryani", type="dish"),
         LovedItem(text="Nusrat Fateh Ali Khan", type="artist")]


class CountingAdapter(QlooAdapter):
    def __init__(self):
        super().__init__(mode="mock")
        self.requests = 0

    async def search_entities(self, *a, **k):
        self.requests += 1
        return await super().search_entities(*a, **k)

    async def recommend(self, *a, **k):
        self.requests += 1
        return await super().recommend(*a, **k)


def new_session(**kw):
    adapter = CountingAdapter()
    p = profile(loved_items=LOVED, **kw)
    summary = asyncio.run(resolver.resolve(adapter, p.loved_items))
    cands, notes = asyncio.run(candidates.build_candidates(adapter, p, summary))
    s = Session(profile=p, resolver=summary, candidates=cands, qloo_notes=notes)
    asyncio.run(pipeline.make_plan(s))
    return s, adapter


def ids(plan):
    return [(i.day, i.slot, i.candidate.id) for i in plan.items]


def act(s, action, item_id=None):
    before = ids(s.plan)
    plan, changes, changed = asyncio.run(feedback.handle(s, action, item_id))
    return before, ids(plan), changes, changed


def test_too_expensive_lowers_budget_and_drops_item():
    s, _ = new_session()
    target = s.plan.items[0].candidate.id
    before, after, changes, changed = act(s, "too_expensive", target)
    assert s.profile.budget_per_activity_cad == 14
    assert target not in [x[2] for x in after]
    assert before != after and changed
    assert any("because budget is now $14 CAD" in c for c in changes)


def test_not_alone_raises_comfort_and_boosts_social():
    s, _ = new_session(comfort="solo_ok")
    social_before = sum(1 for i in s.plan.items if i.candidate.social)
    before, after, changes, _ = act(s, "not_alone")
    assert s.profile.comfort == "small_group" and s.social_boost == 0.5
    assert sum(1 for i in s.plan.items if i.candidate.social) > social_before
    assert before != after


def test_not_alone_never_lowers_social_count():
    s, _ = new_session(comfort="small_group")
    for _ in range(3):
        social_before = sum(1 for i in s.plan.items if i.candidate.social)
        act(s, "not_alone")
        assert sum(1 for i in s.plan.items if i.candidate.social) >= social_before


def test_more_familiar_raises_familiarity():
    s, _ = new_session(familiarity=0.25)
    fam_before = sum(1 for i in s.plan.items if i.candidate.mode == "familiar")
    before, after, _, _ = act(s, "more_familiar")
    assert s.profile.familiarity == 0.5
    assert before != after
    assert sum(1 for i in s.plan.items if i.candidate.mode == "familiar") >= fam_before


def test_repeated_clicks_hit_bounds():
    s, _ = new_session(budget_per_activity_cad=3, comfort="solo_ok", familiarity=0.5)
    for _ in range(6):
        act(s, "too_expensive")
        act(s, "not_alone")
        act(s, "more_familiar")
    assert s.profile.budget_per_activity_cad == 0
    assert s.profile.comfort == "prefer_friend"
    assert s.social_boost == 1.5 and s.min_social == config.MIN_SOCIAL_MAX
    assert s.profile.familiarity == 1.0


def test_replan_makes_no_new_qloo_calls():
    s, adapter = new_session()
    n = adapter.requests
    for a in ("too_expensive", "not_alone", "more_familiar"):
        act(s, a)
    assert adapter.requests == n

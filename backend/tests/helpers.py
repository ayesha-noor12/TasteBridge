from app.models import Candidate, Evidence, Profile


def cand(id, category="food", mode="familiar", source="curated", cost=None, travel=None, social=False,
         recurring=False, solo_only=False, diet=(), rank=None, total=None, hours=None, name=None):
    return Candidate(
        id=id, name=name or id, category=category, mode=mode, source=source,
        cost_cad=cost, travel_minutes=travel, address=None, url=None, verified_on=None,
        diet_tags=list(diet), social=social, recurring=recurring, solo_only=solo_only, duration_hours=hours,
        evidence=Evidence(seed_inputs=["x -> X"] if source == "qloo" else [], qloo_entity=name or id if source == "qloo" else None,
                          qloo_signal=None, city_signal="Toronto", raw=None, qloo_rank=rank, qloo_total=total),
    )


def profile(**kw):
    base = dict(origin="Pakistan", preserve=["food", "music", "friends"], loved_items=[],
                budget_per_activity_cad=20, hours_per_week=12, max_travel_minutes=40,
                diet=["none"], comfort="small_group", familiarity=0.5)
    base.update(kw)
    return Profile(**base)

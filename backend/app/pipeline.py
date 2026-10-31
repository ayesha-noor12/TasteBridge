"""Steps 5-8 of the pipeline: filter -> rank -> plan -> explain. Uses only cached candidates."""

from . import config, explain, filters, planner, ranker
from .models import BridgeResponse, Candidate, Card, CategoryCards, DroppedItem, Plan, PlanItem
from .sessions import Session


def ranked_for(session: Session) -> tuple[list[tuple[Candidate, float]], list[DroppedItem]]:
    kept, dropped = filters.apply(session.candidates, session.profile, session.rejected_ids)
    return ranker.rank(kept, session.profile, session.social_boost), dropped


def bridge(session: Session) -> BridgeResponse:
    """Familiar/Discover cards per category. Uses template explanations (no LLM calls per card)."""
    ranked, dropped = ranked_for(session)
    profile = session.profile
    categories = {}
    for cat, modes in ranker.split_by_category(ranked).items():
        cards = {
            mode: [
                Card(candidate=c, **explain.template(c, profile, explain.why_now_for(c, None, False)).model_dump())
                for c in items
            ]
            for mode, items in modes.items()
        }
        top = [c.id for c, _ in ranked if c.category == cat][:3]
        categories[cat] = CategoryCards(**cards, top_ids=top)
    return BridgeResponse(
        city=config.CITY["name"],
        familiarity=profile.familiarity,
        categories=categories,
        resolver=session.resolver,
        dropped=dropped,
        notes=session.qloo_notes,
    )


async def make_plan(session: Session) -> Plan:
    ranked, dropped = ranked_for(session)
    scheduled, notes = planner.build(ranked, session.profile.hours_per_week, session.min_social, session.profile.familiarity)

    hints = []
    for i, s in enumerate(scheduled):
        anchor = i == 0 and s.candidate.mode == "familiar"
        hints.append(explain.why_now_for(s.candidate, s.day, anchor))

    # Reuse explanations already written for the same item + hint (no repeated LLM calls).
    todo = [(s.candidate, h) for s, h in zip(scheduled, hints) if f"{s.candidate.id}|{h}" not in session.explanations]
    for (c, h), result in zip(todo, await explain.explain_many(todo, session.profile)):
        session.explanations[f"{c.id}|{h}"] = result

    items = []
    for s, h in zip(scheduled, hints):
        exp, src = session.explanations[f"{s.candidate.id}|{h}"]
        items.append(PlanItem(day=s.day, slot=s.slot, candidate=s.candidate, explanation_source=src, **exp.model_dump()))

    if dropped:
        notes.append(f"{len(dropped)} option{'s were' if len(dropped) != 1 else ' was'} removed by your budget, travel, diet or comfort settings.")
    notes.extend(session.qloo_notes)
    plan = Plan(items=items, notes=notes, unverified_count=sum(1 for i in items if filters.is_unverified(i.candidate)))
    session.plan = plan
    return plan

"""Feedback buttons -> constraint/weight updates -> re-plan from cached candidates."""

from . import config, pipeline
from .models import FeedbackAction, Plan
from .sessions import Session

NEXT_COMFORT = {"solo_ok": "small_group", "small_group": "prefer_friend", "prefer_friend": "prefer_friend"}


def apply_action(session: Session, action: FeedbackAction, item_id: str | None) -> str:
    """Mutate the session's profile/weights. Returns the reason used in change messages."""
    p = session.profile
    if action == "too_expensive":
        target = item_id or _most_expensive_item(session)
        if target:
            session.rejected_ids.add(target)
        new_budget = int(p.budget_per_activity_cad * (1 - config.BUDGET_CUT))
        session.profile = p.model_copy(update={"budget_per_activity_cad": max(0, new_budget)})
        return f"budget is now ${session.profile.budget_per_activity_cad} CAD"
    if action == "not_alone":
        session.profile = p.model_copy(update={"comfort": NEXT_COMFORT[p.comfort]})
        session.social_boost = min(config.SOCIAL_BOOST_MAX, session.social_boost + config.SOCIAL_BOOST_STEP)
        # Ask for one more social item than the plan already has, so the click always adds company if it can.
        current = sum(1 for i in session.plan.items if i.candidate.social) if session.plan else 0
        session.min_social = min(config.MIN_SOCIAL_MAX, max(session.min_social, current) + 1)
        return f"you prefer company (comfort: {session.profile.comfort.replace('_', ' ')})"
    if action == "more_familiar":
        new = min(1.0, round(p.familiarity + config.FAMILIARITY_STEP, 2))
        session.profile = p.model_copy(update={"familiarity": new})
        return f"familiarity is now {int(new * 100)}%"
    raise ValueError(f"unknown action {action}")


def _most_expensive_item(session: Session) -> str | None:
    """Without an item_id, reject the priciest known-cost item; else the first plan item."""
    if not session.plan or not session.plan.items:
        return None
    priced = [i for i in session.plan.items if i.candidate.cost_cad is not None]
    if priced:
        return max(priced, key=lambda i: (i.candidate.cost_cad, i.candidate.name)).candidate.id
    return session.plan.items[0].candidate.id


def diff(old: Plan | None, new: Plan, reason: str) -> tuple[list[str], list[str]]:
    """Human-readable change list (by item, not by slot) plus ids of items that are new or moved."""
    old_items = old.items if old else []
    old_ids = {i.candidate.id for i in old_items}
    new_ids = {i.candidate.id for i in new.items}
    removed = [i for i in old_items if i.candidate.id not in new_ids]
    added = [i for i in new.items if i.candidate.id not in old_ids]
    changes = []

    # Pair each removed item with an added one of the same kind first, so "Replaced A with B" reads sensibly.
    added_left = list(added)
    pairs = []
    for before in removed:
        if not added_left:
            break
        match = next((a for a in added_left if (a.candidate.social, a.candidate.category) == (before.candidate.social, before.candidate.category)), None)
        match = match or next((a for a in added_left if a.candidate.social and not before.candidate.social), None) or added_left[0]
        added_left.remove(match)
        pairs.append((before, match))
    removed = [b for b, _ in pairs] + [i for i in removed if all(i is not b for b, _ in pairs)]
    added = [a for _, a in pairs] + added_left
    for before, after in pairs:
        changes.append(f"Replaced {before.candidate.name} with {after.candidate.name} (day {after.day}) because {reason}.")
    for before in removed[len(added):]:
        changes.append(f"Removed {before.candidate.name} because {reason}.")
    for after in added[len(removed):]:
        changes.append(f"Added {after.candidate.name} (day {after.day}) because {reason}.")

    old_pos = {i.candidate.id: (i.day, i.slot) for i in old_items}
    moved = [i for i in new.items if i.candidate.id in old_pos and old_pos[i.candidate.id] != (i.day, i.slot)]
    if moved:
        changes.append(f"{len(moved)} other item{'s' if len(moved) != 1 else ''} moved to a different day to keep the week balanced.")
    changed_ids = [i.candidate.id for i in added + moved]
    if not changes:
        changes.append(f"Settings updated ({reason}); no better options were available, so the plan stayed the same.")
    return changes, changed_ids


async def handle(session: Session, action: FeedbackAction, item_id: str | None) -> tuple[Plan, list[str], list[str]]:
    old = session.plan or await pipeline.make_plan(session)
    reason = apply_action(session, action, item_id)
    new = await pipeline.make_plan(session)
    changes, changed_ids = diff(old, new, reason)
    return new, changes, changed_ids

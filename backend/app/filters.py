"""Hard constraints, applied in code before scoring. Unknown values are kept but flagged."""

from .models import Candidate, DroppedItem, Profile

FLAG_COST = "cost not verified"
FLAG_TRAVEL = "travel time not verified"
FLAG_DIET = "diet suitability not verified"
FLAG_SOURCE = "details not verified"


def required_diet(profile: Profile) -> set[str]:
    return {d for d in profile.diet if d != "none"}


def check(c: Candidate, profile: Profile, rejected_ids: set[str] = frozenset()) -> tuple[str | None, list[str]]:
    """Return (drop_reason or None, flags)."""
    if c.id in rejected_ids:
        return "you marked it as too expensive", []

    flags: list[str] = []
    if c.cost_cad is None:
        flags.append(FLAG_COST)
    elif c.cost_cad > profile.budget_per_activity_cad:
        return f"costs ${c.cost_cad} CAD, over your ${profile.budget_per_activity_cad} CAD budget", []

    if c.travel_minutes is None:
        flags.append(FLAG_TRAVEL)
    elif c.travel_minutes > profile.max_travel_minutes:
        return f"{c.travel_minutes} min away, over your {profile.max_travel_minutes} min limit", []

    need = required_diet(profile)
    if need and c.category == "food":
        if not c.diet_tags:
            flags.append(FLAG_DIET)
        elif not need.issubset(set(c.diet_tags)):
            return f"not tagged {', '.join(sorted(need - set(c.diet_tags)))}", []

    if profile.comfort == "prefer_friend" and c.solo_only:
        return "solo-only activity and you prefer going with someone", []

    if c.source == "unverified":
        flags.append(FLAG_SOURCE)
    return None, flags


def apply(candidates: list[Candidate], profile: Profile, rejected_ids: set[str] = frozenset()) -> tuple[list[Candidate], list[DroppedItem]]:
    kept, dropped = [], []
    for c in candidates:
        reason, flags = check(c, profile, rejected_ids)
        if reason:
            dropped.append(DroppedItem(name=c.name, reason=reason))
        else:
            kept.append(c.model_copy(update={"flags": flags}))
    return kept, dropped


def is_unverified(c: Candidate) -> bool:
    return c.source == "unverified" or FLAG_COST in c.flags or FLAG_TRAVEL in c.flags

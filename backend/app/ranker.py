"""Deterministic scoring and the Familiar/Discover split. Pure functions only."""

from . import config
from .models import Candidate, Profile


def _clip(x: float) -> float:
    return max(0.0, min(1.0, x))


def taste_match(c: Candidate) -> float:
    """Presence and rank of Qloo evidence. 0 for anything Qloo did not return."""
    ev = c.evidence
    if c.source != "qloo" or ev.qloo_rank is None or not ev.qloo_total:
        return 0.0
    return 1.0 - (ev.qloo_rank - 1) / ev.qloo_total


def preserve_match(c: Candidate, profile: Profile) -> float:
    return 1.0 if config.CATEGORY_PRESERVE[c.category] & set(profile.preserve) else 0.0


def affordability(c: Candidate, profile: Profile) -> float:
    if c.cost_cad is None:
        return 0.0  # unknown cost earns nothing
    if profile.budget_per_activity_cad == 0:
        return 1.0 if c.cost_cad == 0 else 0.0
    return _clip(1 - c.cost_cad / profile.budget_per_activity_cad)


def proximity(c: Candidate, profile: Profile) -> float:
    if c.travel_minutes is None:
        return 0.0
    return _clip(1 - c.travel_minutes / profile.max_travel_minutes)


def social_bonus(c: Candidate, profile: Profile) -> float:
    if c.solo_only and profile.comfort != "solo_ok":
        return 0.0
    return 1.0 if (c.social or c.recurring) else 0.0


def score(c: Candidate, profile: Profile, social_boost: float = 0.0) -> float:
    w = config.WEIGHTS
    s = (
        w["taste_match"] * taste_match(c)
        + w["preserve_match"] * preserve_match(c, profile)
        + w["affordability"] * affordability(c, profile)
        + w["proximity"] * proximity(c, profile)
        + w["social_bonus"] * social_bonus(c, profile)
    )
    if c.mode == "familiar":
        s *= 0.5 + profile.familiarity
    else:
        s *= 1.5 - profile.familiarity
    if c.social and social_boost:
        s *= 1 + social_boost
    return round(s, 6)


def rank(candidates: list[Candidate], profile: Profile, social_boost: float = 0.0) -> list[tuple[Candidate, float]]:
    scored = [(c, score(c, profile, social_boost)) for c in candidates]
    return sorted(scored, key=lambda cs: (-cs[1], cs[0].name, cs[0].id))


def split_by_category(ranked: list[tuple[Candidate, float]], per_mode: int = 3) -> dict[str, dict[str, list[Candidate]]]:
    out: dict[str, dict[str, list[Candidate]]] = {}
    for c, _ in ranked:
        bucket = out.setdefault(c.category, {"familiar": [], "discover": []})[c.mode]
        if len(bucket) < per_mode:
            bucket.append(c)
    return out

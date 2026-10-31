"""7-day plan assembly from ranked, already-filtered candidates."""

from dataclasses import dataclass

from . import config
from .models import Candidate

MAX_PER_CATEGORY = 3
DEFAULT_SLOT = {"food": "evening", "music": "evening", "social": "evening", "venue": "evening", "activity": "afternoon"}
SLOT_ORDER = ["morning", "afternoon", "evening"]


@dataclass
class Scheduled:
    day: int
    slot: str
    candidate: Candidate


def item_hours(c: Candidate) -> float:
    return c.duration_hours if c.duration_hours is not None else config.DEFAULT_ITEM_HOURS


def select(ranked: list[tuple[Candidate, float]], hours_per_week: int, min_social: int = 1, familiarity: float = 0.5) -> list[Candidate]:
    chosen: list[Candidate] = []
    used = 0.0

    def take(c: Candidate) -> bool:
        nonlocal used
        if len(chosen) >= config.MAX_PLAN_ITEMS or any(x.id == c.id for x in chosen):
            return False
        if sum(1 for x in chosen if x.category == c.category) >= MAX_PER_CATEGORY:
            return False
        if used + item_hours(c) > hours_per_week:
            return False
        chosen.append(c)
        used += item_hours(c)
        return True

    # Guarantees first, in priority order: familiar anchor, social, discover.
    for wanted in (lambda c: c.mode == "familiar", lambda c: c.social, lambda c: c.mode == "discover"):
        if not any(wanted(x) for x in chosen):
            for c, _ in ranked:
                if wanted(c) and take(c):
                    break
    # "I don't want to go alone" raises the number of guaranteed social items.
    for c, _ in ranked:
        if sum(1 for x in chosen if x.social) >= min_social:
            break
        if c.social:
            take(c)
    # Fill the rest so the share of familiar items follows the slider.
    remaining = [c for c, _ in ranked if c not in chosen]
    while remaining:
        n_familiar = sum(1 for x in chosen if x.mode == "familiar")
        want = "familiar" if n_familiar < familiarity * (len(chosen) + 1) else "discover"
        queue = [c for c in remaining if c.mode == want] + [c for c in remaining if c.mode != want]
        picked = next((c for c in queue if take(c)), None)
        if picked is None:
            break
        remaining.remove(picked)
    return chosen


def order(chosen: list[Candidate], ranked_ids: list[str]) -> list[Candidate]:
    """Gentle familiar anchor first, then familiar, then discover, social later in the week."""
    pos = {cid: i for i, cid in enumerate(ranked_ids)}
    by_rank = sorted(chosen, key=lambda c: pos.get(c.id, 0))
    familiar = [c for c in by_rank if c.mode == "familiar"]
    anchor = next((c for c in familiar if c.category == "food" and not c.social), None) or next(
        (c for c in familiar if not c.social), None
    ) or next(iter(familiar), None)
    rest = [c for c in by_rank if c is not anchor]
    rest.sort(key=lambda c: (c.social, c.mode == "discover", pos.get(c.id, 0)))
    return ([anchor] if anchor else []) + rest


def assign_days(items: list[Candidate]) -> list[Scheduled]:
    n = len(items)
    days = config.PLAN_DAYS
    if n <= days:
        day_list = [1 + round(i * (days - 1) / (n - 1)) if n > 1 else 1 for i in range(n)]
    else:
        extra_days = [6, 7, 5, 4, 3, 2, 1][: n - days]
        day_list = sorted(list(range(1, days + 1)) + extra_days)

    out: list[Scheduled] = []
    used_slots: dict[int, set[str]] = {}
    for c, day in zip(items, day_list):
        taken = used_slots.setdefault(day, set())
        if len(taken) >= config.MAX_ITEMS_PER_DAY:
            continue
        slot = DEFAULT_SLOT[c.category]
        if slot in taken:
            slot = next(s for s in reversed(SLOT_ORDER) if s not in taken)
        taken.add(slot)
        out.append(Scheduled(day=day, slot=slot, candidate=c))
    out.sort(key=lambda s: (s.day, SLOT_ORDER.index(s.slot)))
    return out


def build(
    ranked: list[tuple[Candidate, float]], hours_per_week: int, min_social: int = 1, familiarity: float = 0.5
) -> tuple[list[Scheduled], list[str]]:
    chosen = select(ranked, hours_per_week, min_social, familiarity)
    scheduled = assign_days(order(chosen, [c.id for c, _ in ranked]))

    notes = []
    hours = sum(item_hours(s.candidate) for s in scheduled)
    notes.append(f"{len(scheduled)} activities, about {hours:g} of your {hours_per_week} hours this week.")
    if any(s.candidate.duration_hours is None for s in scheduled):
        notes.append(f"Durations are not verified; each unknown one is counted as {config.DEFAULT_ITEM_HOURS:g} h.")
    if not any(s.candidate.social for s in scheduled):
        notes.append("No social activity fit your current constraints.")
    if not scheduled:
        notes.append("Nothing fit. Try more weekly hours or a higher budget.")
    return scheduled, notes

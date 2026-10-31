"""Qloo recommendations + curated local items -> one Candidate list."""

import json
from pathlib import Path

from . import config
from .models import Candidate, Evidence, Profile, QlooResult, ResolverSummary
from .qloo_adapter import QlooAdapter, QlooNoResult

QLOO_TAKE = 10
QLOO_PLACE_TAKE = 15  # places are asked for a few extra, because hotels and offices are dropped below

# Words in a Qloo place's type/tags that mark it as food rather than a general venue.
# Only used when Qloo gives no primary_genre.
FOOD_WORDS = ("restaurant", "cafe", "café", "bakery", "dessert", "tea", "food", "eatery", "diner")

# Qloo primary_genre ids (urn:tag:genre:place:...) that are something a student can go and do.
FOOD_GENRE = "urn:tag:genre:place:restaurant"
NOT_AN_OUTING = ("banquet_hall",)
VENUE_GENRES = (
    "live_music_venue", "night_club", "music_venue", "concert_hall", "theater", "theatre", "movie_theater",
    "cinema", "comedy_club", "museum", "art_gallery", "gallery", "park", "library", "book_store", "bookstore",
    "community_center", "cultural_center", "market", "farmers_market", "bowling_alley", "arcade",
    "karaoke", "tourist_attraction", "stadium", "board_game", "dance", "event_venue",
)


def curated_label(entry: dict) -> str:
    """'curated' only when a person filled url, address and verified_on; otherwise 'unverified'."""
    return "curated" if all(entry.get(k) for k in ("url", "address", "verified_on")) else "unverified"


def load_curated(path: Path | None = None) -> list[Candidate]:
    path = path or config.DATA_DIR / config.CITY["curated_file"]
    data = json.loads(path.read_text())
    city = config.CITY["name"]
    out = []
    for entry in data["entries"]:
        source = curated_label(entry)
        out.append(
            Candidate(
                id=entry["id"],
                name=entry["name"],
                category=entry["category"],
                mode=entry["mode"],
                source=source,
                cost_cad=entry.get("cost_cad"),
                travel_minutes=entry.get("travel_minutes"),
                address=entry.get("address"),
                url=entry.get("url"),
                verified_on=entry.get("verified_on"),
                diet_tags=entry.get("diet_tags") or [],
                social=bool(entry.get("social")),
                recurring=bool(entry.get("recurring")),
                solo_only=bool(entry.get("solo_only")),
                duration_hours=entry.get("duration_hours"),
                evidence=Evidence(
                    seed_inputs=[],
                    qloo_entity=None,
                    qloo_signal=None,
                    city_signal=f"{city} (hand-curated list)",
                    raw=None,
                ),
            )
        )
    return out


def _place_category(result: QlooResult) -> str | None:
    """'food', 'venue', or None for places that are not an outing (hotels, offices, shops)."""
    genre = result.genre_id
    if genre:
        leaf = genre.rsplit(":", 1)[-1]
        if any(x in leaf for x in NOT_AN_OUTING):
            return None
        if genre.startswith(FOOD_GENRE):
            return "food"
        return "venue" if any(v in leaf for v in VENUE_GENRES) else None
    text = " ".join([result.type or "", *result.tags]).lower()
    return "food" if any(w in text for w in FOOD_WORDS) else "venue"


def _qloo_signal(result: QlooResult) -> str:
    if result.affinity is not None:
        return f"affinity {result.affinity} (as returned by Qloo)"
    return f"rank {result.rank} of {result.total} in Qloo's response (no affinity value returned)"


def qloo_candidate(result: QlooResult, category: str, seeds: list[str], city_signal: str) -> Candidate:
    # Familiar = top half of Qloo's ordering for the user's own seeds; Discover = the rest.
    mode = "familiar" if result.rank <= max(1, (result.total + 1) // 2) else "discover"
    return Candidate(
        id=f"qloo:{result.entity_id}",
        name=result.name,
        category=category,
        mode=mode,
        source="qloo",
        cost_cad=None,
        travel_minutes=None,
        address=result.address,
        url=result.url,
        verified_on=None,
        image_url=result.image_url,
        qloo_facts=result.facts,
        evidence=Evidence(
            seed_inputs=seeds,
            qloo_entity=result.name,
            qloo_signal=_qloo_signal(result),
            city_signal=city_signal,
            raw=result.raw,
            qloo_rank=result.rank,
            qloo_total=result.total,
        ),
    )


async def fetch_qloo_candidates(adapter: QlooAdapter, profile: Profile, summary: ResolverSummary) -> tuple[list[Candidate], list[str]]:
    """Ask Qloo for places (location-filtered) and artists seeded by every resolved entity."""
    notes: list[str] = []
    if not summary.resolved:
        notes.append("No loved items resolved to Qloo entities, so only curated items are shown.")
        return [], notes

    seed_ids = [r.entity.entity_id for r in summary.resolved]
    seeds = [f"{r.input} -> {r.entity.name}" for r in summary.resolved]
    city = config.CITY["qloo_location_query"]
    out: list[Candidate] = []

    try:
        places = await adapter.recommend(seed_ids, "place", city, QLOO_PLACE_TAKE)
    except QlooNoResult:
        places = []
    if not places:
        notes.append(f"Qloo returned no places in {city} for your inputs.")
    skipped = []
    for r in places:
        category = None if r.is_closed else _place_category(r)
        if category is None:
            skipped.append(r.facts.genre if r.facts and r.facts.genre else "closed or unknown type")
            continue
        out.append(qloo_candidate(r, category, seeds, f"{city} (Qloo location filter)"))
    if skipped:
        kinds = ", ".join(sorted({k.lower() for k in skipped}))
        notes.append(f"Skipped {len(skipped)} Qloo place(s) that are not outings ({kinds}).")

    if "music" in profile.preserve or any(r.input_type == "artist" for r in summary.resolved):
        try:
            artists = await adapter.recommend(seed_ids, "artist", None, QLOO_TAKE)
        except QlooNoResult:
            artists = []
        if not artists:
            notes.append("Qloo returned no related artists for your inputs.")
        for r in artists:
            out.append(qloo_candidate(r, "music", seeds, f"not location-filtered (artists); look for {city} shows yourself"))

    return out, notes


async def build_candidates(adapter: QlooAdapter, profile: Profile, summary: ResolverSummary) -> tuple[list[Candidate], list[str]]:
    qloo, notes = await fetch_qloo_candidates(adapter, profile, summary)
    seen = set()
    merged = []
    for c in qloo + load_curated():
        if c.id not in seen:
            seen.add(c.id)
            merged.append(c)
    return merged, notes

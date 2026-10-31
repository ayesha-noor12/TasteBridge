"""Free-text loved items -> Qloo entities (resolved / unresolved split)."""

import asyncio

from .models import LovedItem, ResolvedItem, ResolverSummary, UnresolvedItem, clean_text
from . import config
from .qloo_adapter import QlooAdapter, QlooNoResult

# LovedItem.type -> Qloo search type alias. None = search across all types.
SEARCH_TYPE = {
    "dish": "place",
    "artist": "artist",
    "show": "tv_show",
    "place": "place",
    "activity": None,
}


async def _resolve_one(adapter: QlooAdapter, item: LovedItem) -> ResolvedItem | UnresolvedItem:
    try:
        text = clean_text(item.text, config.MAX_TEXT_LEN)
    except ValueError:
        return UnresolvedItem(input=item.text[: config.MAX_TEXT_LEN], input_type=item.type, reason="input too long")
    if not text:
        return UnresolvedItem(input="", input_type=item.type, reason="empty input")
    try:
        found = await adapter.search_entities(text, SEARCH_TYPE[item.type], take=3)
    except QlooNoResult:
        found = []
    if not found:
        return UnresolvedItem(input=text, input_type=item.type, reason="Qloo returned no matching entity")
    return ResolvedItem(input=text, input_type=item.type, entity=found[0])


async def resolve(adapter: QlooAdapter, items: list[LovedItem]) -> ResolverSummary:
    """Auth/rate-limit/unavailable errors propagate: the caller must show them, not hide them."""
    outcomes = await asyncio.gather(*(_resolve_one(adapter, i) for i in items))
    return ResolverSummary(
        resolved=[o for o in outcomes if isinstance(o, ResolvedItem)],
        unresolved=[o for o in outcomes if isinstance(o, UnresolvedItem)],
    )

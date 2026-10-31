"""All Pydantic schemas used by the API and the pipeline."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from . import config

Source = Literal["qloo", "curated", "unverified"]
Category = Literal["food", "music", "social", "venue", "activity"]
Mode = Literal["familiar", "discover"]
Preserve = Literal["food", "language", "music", "festivals", "friends", "nightlife", "familiarity"]
Diet = Literal["halal", "vegetarian", "vegan", "gluten_free", "none"]
Comfort = Literal["solo_ok", "small_group", "prefer_friend"]
Slot = Literal["morning", "afternoon", "evening"]
FeedbackAction = Literal["too_expensive", "not_alone", "more_familiar"]


def clean_text(value: str, max_len: int) -> str:
    """Strip control characters, collapse whitespace, enforce a length limit."""
    printable = "".join(ch for ch in value if ch.isprintable())
    collapsed = " ".join(printable.split())
    if len(collapsed) > max_len:
        raise ValueError(f"must be at most {max_len} characters")
    return collapsed


class LovedItem(BaseModel):
    text: str
    type: Literal["dish", "artist", "show", "place", "activity"]

    @field_validator("text")
    @classmethod
    def _clean(cls, v: str) -> str:
        return clean_text(v, config.MAX_TEXT_LEN)


class Profile(BaseModel):
    origin: str = Field(min_length=1)
    destination_city: str = config.CITY["name"]
    preserve: list[Preserve] = Field(default_factory=list, max_length=7)
    loved_items: list[LovedItem] = Field(default_factory=list, max_length=config.MAX_LOVED_ITEMS)
    budget_per_activity_cad: int = Field(ge=0, le=200)
    hours_per_week: int = Field(ge=1, le=40)
    max_travel_minutes: int = Field(ge=5, le=120)
    diet: list[Diet] = Field(default_factory=lambda: ["none"])
    comfort: Comfort = "small_group"
    familiarity: float = Field(ge=0, le=1, default=0.5)  # slider: 1 = most familiar

    @field_validator("origin")
    @classmethod
    def _clean_origin(cls, v: str) -> str:
        cleaned = clean_text(v, config.MAX_ORIGIN_LEN)
        if not cleaned:
            raise ValueError("origin must not be empty")
        return cleaned

    @field_validator("destination_city")
    @classmethod
    def _only_demo_city(cls, v: str) -> str:
        if v != config.CITY["name"]:
            raise ValueError(f"only {config.CITY['name']} is supported in this demo")
        return v


# --- Qloo adapter outputs ---


class QlooEntity(BaseModel):
    entity_id: str
    name: str
    type: str | None = None
    image_url: str | None = None  # Qloo's own image (images.qloo.com), if returned
    raw: dict | None = None


class QlooFacts(BaseModel):
    """Venue facts exactly as Qloo returned them (properties.*). Never filled from anywhere else."""

    genre: str | None = None  # primary_genre name, e.g. "West African restaurant"
    rating: float | None = None  # business_rating
    price_level: int | None = None  # 1-4
    neighborhood: str | None = None
    description: str | None = None  # short_description
    hours: dict[str, str] = Field(default_factory=dict)  # weekday -> "12:00-20:30" or "closed"
    live_music: bool = False


class QlooResult(BaseModel):
    entity_id: str
    name: str
    type: str | None = None
    affinity: float | None = None  # as returned by Qloo, if present
    rank: int  # 1-based position in Qloo's response
    total: int  # number of results in that response
    address: str | None = None
    url: str | None = None
    tags: list[str] = Field(default_factory=list)
    image_url: str | None = None
    genre_id: str | None = None  # properties.primary_genre.id, used to keep places that are things to do
    is_closed: bool = False
    facts: QlooFacts | None = None
    raw: dict | None = None


# --- Resolver ---


class ResolvedItem(BaseModel):
    input: str
    input_type: str
    entity: QlooEntity


class UnresolvedItem(BaseModel):
    input: str
    input_type: str
    reason: str


class ResolverSummary(BaseModel):
    resolved: list[ResolvedItem]
    unresolved: list[UnresolvedItem]


# --- Candidates, plan ---


class Evidence(BaseModel):
    seed_inputs: list[str]
    qloo_entity: str | None
    qloo_signal: str | None  # Qloo's own relevance signal, shown as given
    city_signal: str
    raw: dict | None
    qloo_rank: int | None = None
    qloo_total: int | None = None


class Candidate(BaseModel):
    id: str
    name: str
    category: Category
    mode: Mode
    source: Source
    cost_cad: int | None
    travel_minutes: int | None
    address: str | None
    url: str | None
    verified_on: str | None
    diet_tags: list[str] = Field(default_factory=list)
    social: bool = False
    recurring: bool = False
    solo_only: bool = False
    duration_hours: float | None = None
    image_url: str | None = None  # only from Qloo (images.qloo.com); never invented
    qloo_facts: QlooFacts | None = None  # rating, price level, hours... only for Qloo results
    evidence: Evidence
    flags: list[str] = Field(default_factory=list)  # e.g. "cost not verified"


class Explanation(BaseModel):
    why_this: str
    why_here: str
    why_now: str


class PlanItem(BaseModel):
    day: int
    slot: Slot
    candidate: Candidate
    why_this: str
    why_here: str
    why_now: str
    explanation_source: Literal["ai", "template"] = "template"


class Plan(BaseModel):
    items: list[PlanItem]
    notes: list[str]
    unverified_count: int


# --- API request / response bodies ---


class SessionResponse(BaseModel):
    session_id: str
    resolver: ResolverSummary
    qloo_mode: str


class SessionRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=64)


class FeedbackRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=64)
    action: FeedbackAction
    item_id: str | None = Field(default=None, max_length=200)


class FamiliarityRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=64)
    value: float = Field(ge=0, le=1)


class Card(BaseModel):
    candidate: Candidate
    why_this: str
    why_here: str
    why_now: str
    explanation_source: Literal["ai", "template"] = "template"


class CategoryCards(BaseModel):
    familiar: list[Card]
    discover: list[Card]
    top_ids: list[str] = Field(default_factory=list)  # mixed ranking at the current slider value


class DroppedItem(BaseModel):
    name: str
    reason: str


class BridgeResponse(BaseModel):
    city: str
    familiarity: float
    categories: dict[str, CategoryCards]
    resolver: ResolverSummary
    dropped: list[DroppedItem]
    notes: list[str]


class PlanResponse(BaseModel):
    plan: Plan
    profile: Profile


class FeedbackResponse(BaseModel):
    plan: Plan
    profile: Profile
    changes: list[str]
    changed_ids: list[str]


class BaselineSuggestion(BaseModel):
    name: str
    description: str = ""


class BaselineResult(BaseModel):
    available: bool
    label: str = "Unverified, LLM-only"
    suggestions: list[BaselineSuggestion] = Field(default_factory=list)
    raw_text: str | None = None
    message: str | None = None


class CompareResponse(BaseModel):
    baseline: BaselineResult
    tastebridge: list[PlanItem]
    resolver: ResolverSummary

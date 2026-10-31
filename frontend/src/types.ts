// Mirrors backend/app/models.py.

export type Source = "qloo" | "curated" | "unverified";
export type Mode = "familiar" | "discover";
export type Category = "food" | "music" | "social" | "venue" | "activity";
export type ItemType = "dish" | "artist" | "show" | "place" | "activity";
export type Comfort = "solo_ok" | "small_group" | "prefer_friend";
export type FeedbackAction = "too_expensive" | "not_alone" | "more_familiar";

export interface LovedItem { text: string; type: ItemType }

export interface Profile {
  origin: string;
  destination_city: string;
  preserve: string[];
  loved_items: LovedItem[];
  budget_per_activity_cad: number;
  hours_per_week: number;
  max_travel_minutes: number;
  diet: string[];
  comfort: Comfort;
  familiarity: number;
}

export interface Evidence {
  seed_inputs: string[];
  qloo_entity: string | null;
  qloo_signal: string | null;
  city_signal: string;
  raw: Record<string, unknown> | null;
  qloo_rank: number | null;
  qloo_total: number | null;
}

export interface QlooFacts {
  genre: string | null;
  rating: number | null;
  price_level: number | null;
  neighborhood: string | null;
  description: string | null;
  hours: Record<string, string>;
  live_music: boolean;
}

export interface Candidate {
  id: string;
  name: string;
  category: Category;
  mode: Mode;
  source: Source;
  cost_cad: number | null;
  travel_minutes: number | null;
  address: string | null;
  url: string | null;
  verified_on: string | null;
  diet_tags: string[];
  social: boolean;
  recurring: boolean;
  solo_only: boolean;
  duration_hours: number | null;
  image_url: string | null;
  qloo_facts?: QlooFacts | null;
  evidence: Evidence;
  flags: string[];
}

export interface Explained {
  why_this: string;
  why_here: string;
  why_now: string;
  explanation_source: "ai" | "template";
}

export interface Card extends Explained { candidate: Candidate }
export interface PlanItem extends Explained { day: number; slot: "morning" | "afternoon" | "evening"; candidate: Candidate }
export interface Plan { items: PlanItem[]; notes: string[]; unverified_count: number }

export interface ResolverSummary {
  resolved: { input: string; input_type: string; entity: { entity_id: string; name: string; type: string | null; image_url: string | null } }[];
  unresolved: { input: string; input_type: string; reason: string }[];
}

export interface BridgeResponse {
  city: string;
  familiarity: number;
  categories: Record<string, { familiar: Card[]; discover: Card[]; top_ids: string[] }>;
  resolver: ResolverSummary;
  dropped: { name: string; reason: string }[];
  notes: string[];
}

export interface FeedbackResponse { plan: Plan; profile: Profile; changes: string[]; changed_ids: string[] }

export interface CompareResponse {
  baseline: { available: boolean; label: string; suggestions: { name: string; description: string }[]; raw_text: string | null; message: string | null };
  tastebridge: PlanItem[];
  resolver: ResolverSummary;
}

export interface Health {
  status: string;
  version: string;
  city: string;
  qloo_mode: "live" | "mock";
  qloo_calls_used: number;
  qloo_cache_hits: number;
  llm_mode: "on" | "off";
}

export interface Presets {
  demo_profile: Profile;
  preserve_chips: string[];
  item_types: ItemType[];
  example_items: LovedItem[];
  diets: string[];
  comfort_levels: Comfort[];
  limits: { max_loved_items: number; max_text_len: number };
}

export interface Cohort {
  label: string;
  cohort: string;
  clusters: { label: string; count: number; suggested_event: string }[];
}

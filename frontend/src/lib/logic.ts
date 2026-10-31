import type { FeedbackAction, Health, Source } from "../types";

export const SOURCE_BADGE: Record<Source, { label: string; className: string; title: string }> = {
  qloo: {
    label: "Qloo-matched",
    className: "bg-teal-100 text-teal-800 border-teal-700/40",
    title: "Returned by Qloo for your inputs and city.",
  },
  curated: {
    label: "Curated",
    className: "bg-amber-100 text-amber-800 border-amber-800/30",
    title: "Hand-checked local item with a source and a verification date.",
  },
  unverified: {
    label: "Unverified",
    className: "bg-white text-clay-700 border-clay-700/50 border-dashed",
    title: "Not confirmed. Check details yourself before going.",
  },
};

export function badgeFor(source: string) {
  return SOURCE_BADGE[source as Source] ?? SOURCE_BADGE.unverified;
}

export function clampFamiliarity(value: number): number {
  if (Number.isNaN(value)) return 0.5;
  return Math.round(Math.min(1, Math.max(0, value)) * 100) / 100;
}

export function sliderLabel(value: number): string {
  const v = clampFamiliarity(value);
  if (v <= 0.2) return "Mostly new things";
  if (v < 0.45) return "Lean towards new";
  if (v <= 0.55) return "Balanced";
  if (v < 0.8) return "Lean towards familiar";
  return "Mostly familiar";
}

export interface FeedbackButton {
  action: FeedbackAction;
  label: string;
  hint: string;
}

export const FEEDBACK_BUTTONS: FeedbackButton[] = [
  { action: "too_expensive", label: "Too expensive", hint: "Lowers your budget by 30% and removes the selected item." },
  { action: "not_alone", label: "I don't want to go alone", hint: "Prefers group activities and adds more social options." },
  { action: "more_familiar", label: "More familiar", hint: "Moves the slider 25% towards familiar." },
];

/** "Too expensive" needs a target: the selected item, otherwise the backend picks one. */
export function feedbackTarget(action: FeedbackAction, selectedId: string | null): string | undefined {
  return action === "too_expensive" && selectedId ? selectedId : undefined;
}

export function feedbackDisabled(familiarity: number, action: FeedbackAction, comfort: string): boolean {
  if (action === "more_familiar") return familiarity >= 1;
  if (action === "not_alone") return comfort === "prefer_friend";
  return false;
}

export function formatCad(value: number | null): string {
  return value === null ? "Cost not verified" : value === 0 ? "Free ($0 CAD)" : `$${value} CAD`;
}

export function formatMinutes(value: number | null): string {
  return value === null ? "Travel time not verified" : `${value} min away`;
}

const WEEKDAYS = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"];

/** Today's opening hours from Qloo's weekly hours, e.g. "Open today 12:00-20:30". Null when Qloo gave none. */
export function hoursToday(hours: Record<string, string> | undefined, now: Date = new Date()): string | null {
  const today = hours?.[WEEKDAYS[now.getDay()]];
  if (!today) return null;
  return today === "closed" ? "Closed today" : `Open today ${today.replace(/-/g, "–")}`;
}

/** Google Maps search link for a real address Qloo or a curator supplied. Never built without one. */
export function mapsLink(name: string, address: string | null): string | null {
  return address ? `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${name}, ${address}`)}` : null;
}

export type BannerKind = "demo" | "qloo_down" | "llm_off";

export function bannersFor(health: Health | null, errorCode: string | null): BannerKind[] {
  const out: BannerKind[] = [];
  if (health?.qloo_mode === "mock") out.push("demo");
  if (errorCode && errorCode.startsWith("qloo_") && errorCode !== "qloo_no_result") out.push("qloo_down");
  if (health && health.llm_mode === "off") out.push("llm_off");
  return out;
}

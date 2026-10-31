import type { BridgeResponse, Cohort, CompareResponse, FeedbackAction, FeedbackResponse, Health, Plan, Presets, Profile, ResolverSummary } from "./types";

export class ApiError extends Error {
  constructor(public code: string, message: string) {
    super(message);
  }
}

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(path, { headers: { "Content-Type": "application/json" }, ...init });
  } catch {
    throw new ApiError("network", "Could not reach the TasteBridge server.");
  }
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    const err = body?.error;
    throw new ApiError(err?.code ?? `http_${res.status}`, err?.message ?? `Request failed (${res.status}).`);
  }
  return body as T;
}

const post = <T>(path: string, data: unknown) => call<T>(path, { method: "POST", body: JSON.stringify(data) });

export const api = {
  health: () => call<Health>("/api/health"),
  presets: () => call<Presets>("/api/presets"),
  createSession: (p: Profile) => post<{ session_id: string; resolver: ResolverSummary; qloo_mode: string }>("/api/session", p),
  deleteSession: (sid: string) => call<{ deleted: boolean }>(`/api/session/${encodeURIComponent(sid)}`, { method: "DELETE" }),
  bridge: (sid: string) => post<BridgeResponse>("/api/bridge", { session_id: sid }),
  plan: (sid: string) => post<{ plan: Plan; profile: Profile }>("/api/plan", { session_id: sid }),
  feedback: (sid: string, action: FeedbackAction, itemId?: string) =>
    post<FeedbackResponse>("/api/feedback", { session_id: sid, action, item_id: itemId ?? null }),
  familiarity: (sid: string, value: number) => post<BridgeResponse>("/api/familiarity", { session_id: sid, value }),
  compare: (sid: string) => call<CompareResponse>(`/api/compare/${encodeURIComponent(sid)}`),
  cohort: () => call<Cohort>("/api/admin/cohort"),
};

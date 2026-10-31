import { useEffect, useRef, useState } from "react";
import { api, ApiError } from "./api";
import type { BridgeResponse, Cohort, CompareResponse, FeedbackAction, Health, Plan as PlanT, Presets, Profile } from "./types";
import { Banner } from "./components/Banner";
import { bannersFor } from "./lib/logic";
import { Onboarding } from "./pages/Onboarding";
import { Bridge } from "./pages/Bridge";
import { Plan } from "./pages/Plan";
import { Compare } from "./pages/Compare";
import { Admin } from "./pages/Admin";
import { Icon } from "./components/Icon";

type Page = "onboarding" | "bridge" | "plan" | "compare" | "admin";

const EMPTY_PROFILE: Profile = {
  origin: "",
  destination_city: "Toronto",
  preserve: [],
  loved_items: [],
  budget_per_activity_cad: 20,
  hours_per_week: 10,
  max_travel_minutes: 40,
  diet: ["none"],
  comfort: "small_group",
  familiarity: 0.5,
};

export default function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const [presets, setPresets] = useState<Presets | null>(null);
  const [page, setPage] = useState<Page>("onboarding");
  const [sid, setSid] = useState<string | null>(null);
  const [profile, setProfile] = useState<Profile>(EMPTY_PROFILE);
  const [bridge, setBridge] = useState<BridgeResponse | null>(null);
  const [plan, setPlan] = useState<PlanT | null>(null);
  const [changes, setChanges] = useState<string[]>([]);
  const [changedIds, setChangedIds] = useState<string[]>([]);
  const [compare, setCompare] = useState<CompareResponse | null>(null);
  const [cohort, setCohort] = useState<Cohort | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<{ code: string; message: string } | null>(null);
  const sliderTimer = useRef<number>();

  const refreshHealth = () => api.health().then(setHealth).catch(() => setHealth(null));

  useEffect(() => {
    refreshHealth();
    api.presets().then(setPresets).catch((e: ApiError) => setError({ code: e.code, message: e.message }));
  }, []);

  async function run<T>(fn: () => Promise<T>): Promise<T | null> {
    setBusy(true);
    setError(null);
    try {
      return await fn();
    } catch (e) {
      const err = e instanceof ApiError ? e : new ApiError("unknown", String(e));
      setError({ code: err.code, message: err.message });
      if (err.code === "session_not_found") reset(false);
      return null;
    } finally {
      setBusy(false);
      refreshHealth();
    }
  }

  async function build(p: Profile) {
    const res = await run(async () => {
      const s = await api.createSession(p);
      const b = await api.bridge(s.session_id);
      return { s, b };
    });
    if (!res) return;
    setSid(res.s.session_id);
    setProfile(p);
    setBridge(res.b);
    setPlan(null);
    setCompare(null);
    setChanges([]);
    setChangedIds([]);
    setPage("bridge");
    window.scrollTo({ top: 0 });
  }

  function onFamiliarity(v: number) {
    setProfile((p) => ({ ...p, familiarity: v }));
    window.clearTimeout(sliderTimer.current);
    sliderTimer.current = window.setTimeout(async () => {
      if (!sid) return;
      const b = await run(() => api.familiarity(sid, v));
      if (b) {
        setBridge(b);
        setPlan(null); // re-plan on next visit with the new slider value
        setCompare(null);
      }
    }, 250);
  }

  async function openPlan() {
    setPage("plan");
    if (sid && !plan) {
      const r = await run(() => api.plan(sid));
      if (r) {
        setPlan(r.plan);
        setProfile(r.profile);
        setChanges([]);
        setChangedIds([]);
      }
    }
  }

  async function onFeedback(action: FeedbackAction, itemId?: string) {
    if (!sid) return;
    const r = await run(() => api.feedback(sid, action, itemId));
    if (r) {
      setPlan(r.plan);
      setProfile(r.profile);
      setChanges(r.changes);
      setChangedIds(r.changed_ids);
      setCompare(null);
      setBridge(null);
    }
  }

  async function openBridge() {
    setPage("bridge");
    if (sid && !bridge) {
      const b = await run(() => api.bridge(sid));
      if (b) setBridge(b);
    }
  }

  async function openCompare() {
    setPage("compare");
    if (sid && !compare) {
      const c = await run(() => api.compare(sid));
      if (c) setCompare(c);
    }
  }

  async function retryCompare() {
    if (!sid) return;
    const c = await run(() => api.compare(sid));
    if (c) setCompare(c);
  }

  async function openAdmin() {
    setPage("admin");
    if (!cohort) {
      const c = await run(() => api.cohort());
      if (c) setCohort(c);
    }
  }

  function reset(callServer = true) {
    if (callServer && sid) api.deleteSession(sid).catch(() => undefined);
    setSid(null);
    setBridge(null);
    setPlan(null);
    setCompare(null);
    setChanges([]);
    setChangedIds([]);
    setProfile(EMPTY_PROFILE);
    setPage("onboarding");
  }

  const tabs: { id: Page; label: string; open: () => void; needsSession: boolean }[] = [
    { id: "onboarding", label: "Profile", open: () => setPage("onboarding"), needsSession: false },
    { id: "bridge", label: "Bridge", open: openBridge, needsSession: true },
    { id: "plan", label: "7-day plan", open: openPlan, needsSession: true },
    { id: "compare", label: "Compare", open: openCompare, needsSession: true },
    { id: "admin", label: "Admin", open: openAdmin, needsSession: false },
  ];

  const city = health?.city ?? "Toronto";

  return (
    <div className="min-h-screen">
      <header className="no-print sticky top-0 z-20 border-b border-ink/5 bg-cream/85 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-4 gap-y-2 px-4 py-3">
          <button type="button" onClick={() => setPage("onboarding")} className="flex items-center gap-2" aria-label="TasteBridge home">
            <svg viewBox="0 0 32 32" className="h-8 w-8" aria-hidden="true">
              <circle cx="16" cy="16" r="16" fill="#1f5f5b" />
              <path d="M6 22a10 10 0 0 1 20 0Z" fill="#e9a777" />
              <path d="M16 6v4M8.5 9l2.2 3M23.5 9l-2.2 3" stroke="#fbe3cf" strokeWidth="2" strokeLinecap="round" />
            </svg>
            <span className="font-display text-xl font-semibold text-teal-800">TasteBridge</span>
          </button>
          <nav aria-label="Pages" className="order-3 flex w-full gap-1 overflow-x-auto rounded-full bg-sand/80 p-1 sm:order-none sm:ml-4 sm:w-auto">
            {tabs.map((t) => (
              <button
                key={t.id}
                type="button"
                disabled={t.needsSession && !sid}
                aria-current={page === t.id ? "page" : undefined}
                onClick={t.open}
                className={`whitespace-nowrap rounded-full px-4 py-1.5 text-sm font-medium transition disabled:opacity-35 ${page === t.id ? "bg-paper text-teal-800 shadow-sm" : "text-ink/80 hover:text-ink"}`}
              >
                {t.label}
              </button>
            ))}
          </nav>
          <div className="ml-auto flex items-center gap-2">
            {health && (
              <span className={`pill hidden sm:inline-flex ${health.qloo_mode === "live" ? "bg-teal-100 text-teal-800" : "bg-clay-100 text-clay-700"}`}>
                <span className={`h-1.5 w-1.5 rounded-full ${health.qloo_mode === "live" ? "bg-teal-700" : "bg-clay-700"}`} />
                Qloo {health.qloo_mode}
              </span>
            )}
            {sid && (
              <button type="button" className="btn-ghost px-3 py-1.5" onClick={() => reset()}>
                Reset my profile
              </button>
            )}
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-7xl px-4 py-6">
        <Banner kinds={bannersFor(health, error?.code ?? null)} />
        {error && page !== "onboarding" && (
          <p role="alert" className="mt-3 rounded-2xl border border-clay-700/40 bg-clay-100 p-3 text-sm text-clay-700">{error.message}</p>
        )}

        <main key={page} className="mt-6 animate-rise">
          {page === "onboarding" && presets && (
            <Onboarding key={sid ?? "new"} presets={presets} initial={profile} busy={busy} error={error?.message ?? null} onSubmit={build} />
          )}
          {page === "onboarding" && !presets && !error && <p>Loading…</p>}
          {page === "bridge" && bridge && (
            <Bridge data={bridge} profile={profile} health={health} onFamiliarity={onFamiliarity} onPlan={openPlan} busy={busy} />
          )}
          {page === "plan" && plan && (
            <Plan plan={plan} profile={profile} city={city} changes={changes} changedIds={changedIds} busy={busy} onFeedback={onFeedback} />
          )}
          {page === "compare" && compare && <Compare data={compare} llmOn={health?.llm_mode === "on"} busy={busy} onRetry={retryCompare} />}
          {page === "admin" && cohort && <Admin data={cohort} />}
          {busy && page !== "onboarding" && (
            <p className="mt-4 inline-flex items-center gap-2 text-sm text-ink/70" aria-live="polite">
              <Icon name="spark" className="h-4 w-4 animate-spin text-clay-700" /> Working…
            </p>
          )}
        </main>

        <footer className="mt-16 border-t border-ink/10 pt-6 text-sm text-ink/70">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="max-w-xl">
              <p className="font-display text-lg font-semibold text-teal-800">TasteBridge</p>
              <p className="mt-1">Helps you discover culture and social opportunities; it does not measure wellbeing.</p>
            </div>
            <ul className="space-y-1 text-xs">
              <li><strong>Qloo-matched</strong>: returned by Qloo for your inputs</li>
              <li><strong>Curated</strong>: hand-checked, with a source and date</li>
              <li><strong>Unverified</strong>: check details before going</li>
            </ul>
          </div>
          <p className="mt-4 text-xs">
            Qloo mode: {health?.qloo_mode ?? "?"} · Qloo calls this run: {health?.qloo_calls_used ?? "?"} · Illustrations drawn for this project · v{health?.version ?? "?"}
          </p>
        </footer>
      </div>
    </div>
  );
}

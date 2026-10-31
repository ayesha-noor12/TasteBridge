import type { BridgeResponse, Health, ItemType, Profile } from "../types";
import { SEARCH_AS } from "../lib/categories";
import { Icon } from "./Icon";

interface Props {
  data: BridgeResponse;
  profile: Profile;
  health: Health | null;
}

/** What Qloo was asked and what came back, built only from the bridge response and /api/health. */
export function TracePanel({ data, profile, health }: Props) {
  const cards = Object.values(data.categories).flatMap((g) => [...g.familiar, ...g.discover]);
  const qloo = cards.filter((c) => c.candidate.source === "qloo");
  const placeCards = qloo.filter((c) => c.candidate.evidence.city_signal.includes("location filter")).length;
  const artistCards = qloo.filter((c) => c.candidate.evidence.city_signal.startsWith("not location-filtered")).length;
  const localCards = cards.length - qloo.length;
  const { resolved, unresolved } = data.resolver;
  // Same rule as backend candidates.fetch_qloo_candidates.
  const askedArtists = resolved.length > 0 && (profile.preserve.includes("music") || resolved.some((r) => r.input_type === "artist"));

  return (
    <details open className="card group overflow-hidden">
      <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-5 py-4">
        <span>
          <span className="block font-display text-lg font-semibold">Qloo trace</span>
          <span className="block text-xs text-ink/70">What Qloo was asked, and what came back.</span>
        </span>
        <Icon name="chevron" className="h-5 w-5 shrink-0 transition group-open:rotate-180" />
      </summary>

      <ol className="space-y-5 border-t border-ink/10 px-5 py-5 text-sm">
        <li>
          <h3 className="mb-2 flex items-center gap-2 font-sans text-sm font-semibold">
            <span className="grid h-6 w-6 place-items-center rounded-full bg-teal-700 text-xs text-white">1</span>
            Search: your inputs → Qloo entities
          </h3>
          <ul className="space-y-1.5">
            {resolved.map((r) => (
              <li key={r.input} className="rounded-xl bg-teal-100/60 px-3 py-2">
                <div className="flex flex-wrap items-center gap-x-1.5">
                  <span className="font-medium">{r.input}</span>
                  <Icon name="arrow" className="h-3.5 w-3.5 text-ink/70" />
                  <span className="inline-flex items-center gap-1 font-semibold text-teal-800"><Icon name="check" className="h-3.5 w-3.5" />{r.entity.name}</span>
                </div>
                <p className="text-xs text-ink/70">searched as {SEARCH_AS[r.input_type as ItemType] ?? r.input_type}</p>
              </li>
            ))}
            {unresolved.map((r) => (
              <li key={r.input || "empty"} className="rounded-xl border border-dashed border-clay-700/40 px-3 py-2">
                <div className="flex flex-wrap items-center gap-x-1.5">
                  <span className="font-medium">{r.input || "(empty)"}</span>
                  <Icon name="arrow" className="h-3.5 w-3.5 text-ink/70" />
                  <span className="inline-flex items-center gap-1 font-semibold text-clay-700"><Icon name="x" className="h-3.5 w-3.5" />no match</span>
                </div>
                <p className="text-xs text-ink/70">{r.reason}</p>
              </li>
            ))}
            {!resolved.length && !unresolved.length && <li className="text-ink/70">No loved items entered, so Qloo was not searched.</li>}
          </ul>
        </li>

        <li>
          <h3 className="mb-2 flex items-center gap-2 font-sans text-sm font-semibold">
            <span className="grid h-6 w-6 place-items-center rounded-full bg-teal-700 text-xs text-white">2</span>
            Recommend: matched entities → {data.city}
          </h3>
          {resolved.length === 0 ? (
            <p className="text-ink/70">Skipped: no input matched a Qloo entity.</p>
          ) : (
            <>
              <p className="mb-2 text-xs text-ink/70">All {resolved.length} matched entities were sent together as seeds.</p>
              <table className="w-full text-left text-xs">
                <thead className="text-ink/70">
                  <tr><th className="pb-1 font-medium">Asked for</th><th className="pb-1 font-medium">City used</th><th className="pb-1 text-right font-medium">Cards</th></tr>
                </thead>
                <tbody>
                  <tr className="border-t border-ink/10">
                    <td className="py-1.5 font-medium">Places</td><td>{data.city} (location filter)</td><td className="text-right font-semibold">{placeCards}</td>
                  </tr>
                  <tr className="border-t border-ink/10">
                    <td className="py-1.5 font-medium">Artists</td>
                    <td>{askedArtists ? "none (artists are not location-filtered)" : "not asked (no music input)"}</td>
                    <td className="text-right font-semibold">{askedArtists ? artistCards : "–"}</td>
                  </tr>
                </tbody>
              </table>
            </>
          )}
        </li>

        <li>
          <h3 className="mb-2 flex items-center gap-2 font-sans text-sm font-semibold">
            <span className="grid h-6 w-6 place-items-center rounded-full bg-ink/70 text-xs text-white">3</span>
            Local list (not Qloo)
          </h3>
          <p className="text-ink/70">{localCards} cards from the hand-curated {data.city} list.</p>
          {data.dropped.length > 0 && <p className="mt-1 text-ink/70">{data.dropped.length} options set aside by your budget, travel, diet or comfort limits.</p>}
        </li>
      </ol>

      <p className="border-t border-ink/10 bg-sand/50 px-5 py-3 text-xs text-ink/70">
        Qloo calls since the server started (from /api/health):{" "}
        {health ? <><strong>{health.qloo_calls_used}</strong> live, <strong>{health.qloo_cache_hits}</strong> answered from cache</> : "unavailable"}
        {health?.qloo_mode === "mock" && " · mock mode: no real Qloo calls"}.
      </p>
    </details>
  );
}

import type { BridgeResponse, Health, Profile } from "../types";
import { BridgeCard } from "../components/BridgeCard";
import { Icon, type IconName } from "../components/Icon";
import { FamiliaritySlider } from "../components/Slider";
import { TracePanel } from "../components/TracePanel";
import { CATEGORY } from "../lib/categories";

const ORDER = ["food", "music", "social", "venue", "activity"] as const;

interface Props {
  data: BridgeResponse;
  profile: Profile;
  health: Health | null;
  onFamiliarity: (v: number) => void;
  onPlan: () => void;
  busy: boolean;
}

export function Bridge({ data, profile, health, onFamiliarity, onPlan, busy }: Props) {
  const cats = ORDER.filter((c) => data.categories[c]);
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="eyebrow">{profile.origin ? `From ${profile.origin} to ${data.city}` : "Your bridge"}</p>
          <h1 className="font-display text-3xl font-semibold sm:text-4xl">What you love, in {data.city}</h1>
        </div>
        <button type="button" className="btn-primary no-print" onClick={onPlan}>
          See my 7-day plan <Icon name="arrow" />
        </button>
      </div>

      <TasteStrip data={data} profile={profile} />

      <div className="grid items-start gap-6 lg:grid-cols-[360px,1fr]">
        <TracePanel data={data} profile={profile} health={health} />

        <div className="min-w-0 space-y-8">
          <div className="panel no-print">
            <FamiliaritySlider value={profile.familiarity} onChange={onFamiliarity} />
            <p className="mt-1 text-xs text-ink/70" aria-live="polite">{busy ? "Re-ranking…" : "Ranking updates as you move the slider."}</p>
          </div>

          {data.notes.map((n) => <p key={n} className="rounded-2xl bg-paper px-4 py-2 text-sm text-ink/80">{n}</p>)}

          {cats.map((cat) => {
            const group = data.categories[cat];
            const lead = group.top_ids[0];
            const style = CATEGORY[cat];
            return (
              <section key={cat} aria-labelledby={`cat-${cat}`}>
                <h2 id={`cat-${cat}`} className="mb-3 flex items-center gap-2.5 font-display text-2xl font-semibold">
                  <span className={`grid h-9 w-9 place-items-center rounded-full ${style.chip}`}><Icon name={cat as IconName} className="h-4 w-4" /></span>
                  {style.label}
                </h2>
                <div className="grid gap-4 xl:grid-cols-2">
                  {(["familiar", "discover"] as const).map((mode) => (
                    <div key={mode} className="min-w-0 space-y-3">
                      <h3 className={`font-sans text-xs font-bold uppercase tracking-widest ${mode === "familiar" ? "text-teal-700" : "text-clay-700"}`}>
                        {mode === "familiar" ? "A taste of home" : "Something new"}
                      </h3>
                      {group[mode].length === 0 && <p className="rounded-2xl border border-dashed border-ink/20 p-4 text-sm text-ink/70">No {mode} options fit your settings.</p>}
                      {group[mode].map((card) => (
                        <BridgeCard key={card.candidate.id} c={card.candidate} ex={card} leading={card.candidate.id === lead} />
                      ))}
                    </div>
                  ))}
                </div>
              </section>
            );
          })}

          {data.dropped.length > 0 && (
            <details className="panel text-sm">
              <summary className="cursor-pointer font-semibold">{data.dropped.length} options set aside by your limits</summary>
              <ul className="mt-2 list-disc space-y-0.5 pl-5 text-ink/80">
                {data.dropped.map((d) => <li key={d.name}>{d.name}: {d.reason}</li>)}
              </ul>
            </details>
          )}
        </div>
      </div>
    </div>
  );
}

/** The user's taste in plain words: what they typed, what Qloo matched it to, and their limits. */
function TasteStrip({ data, profile }: { data: BridgeResponse; profile: Profile }) {
  const comfort = profile.comfort === "solo_ok" ? "fine going alone" : profile.comfort === "small_group" ? "small groups" : "prefers going with a friend";
  return (
    <section aria-labelledby="taste-title" className="panel">
      <h2 id="taste-title" className="eyebrow">Your taste, as Qloo understood it</h2>
      <ul className="mt-3 flex flex-wrap gap-2">
        {data.resolver.resolved.map((r) => (
          <li key={r.input} className="pill bg-teal-100 text-teal-800">
            <Icon name="check" className="h-3 w-3" />
            {r.input.toLowerCase() === r.entity.name.toLowerCase() ? r.entity.name : `${r.input} → ${r.entity.name}`}
          </li>
        ))}
        {data.resolver.unresolved.map((u) => (
          <li key={u.input} className="pill border border-dashed border-clay-700 bg-white text-clay-700" title="Qloo found no match, so this did not shape your results">
            <Icon name="x" className="h-3 w-3" />{u.input} (no Qloo match)
          </li>
        ))}
      </ul>
      <p className="mt-3 text-sm text-ink/80">
        Keeping from home: <strong>{profile.preserve.length ? profile.preserve.join(", ") : "nothing chosen"}</strong> · ${profile.budget_per_activity_cad} per outing ·{" "}
        {profile.hours_per_week} h a week · up to {profile.max_travel_minutes} min travel · {comfort}
      </p>
    </section>
  );
}

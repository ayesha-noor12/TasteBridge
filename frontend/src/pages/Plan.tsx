import { useState } from "react";
import type { FeedbackAction, Plan as PlanT, PlanItem, Profile } from "../types";
import { BridgeCard } from "../components/BridgeCard";
import { FeedbackBar } from "../components/FeedbackBar";
import { Icon } from "../components/Icon";
import { CATEGORY, categoryStyle } from "../lib/categories";
import { feedbackTarget } from "../lib/logic";

interface Props {
  plan: PlanT;
  profile: Profile;
  city: string;
  changes: string[];
  changedIds: string[];
  busy: boolean;
  onFeedback: (a: FeedbackAction, itemId?: string) => void;
}

const DAYS = [1, 2, 3, 4, 5, 6, 7];

export function Plan({ plan, profile, city, changes, changedIds, busy, onFeedback }: Props) {
  const [selected, setSelected] = useState<string | null>(null);
  const selectedName = plan.items.find((i) => i.candidate.id === selected)?.candidate.name ?? null;
  const byDay = (d: number): PlanItem[] => plan.items.filter((i) => i.day === d);
  const social = plan.items.filter((i) => i.candidate.social).length;
  const used = new Set(plan.items.map((i) => i.candidate.category));

  return (
    <div>
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="eyebrow">Your plan</p>
          <h1 className="font-display text-3xl font-semibold sm:text-4xl">Your first week in {city}</h1>
          <p className="mt-1 text-sm text-ink/70">
            {plan.items.length} activities, {social} with other people · budget ${profile.budget_per_activity_cad} CAD · {profile.hours_per_week} h/week · familiarity {Math.round(profile.familiarity * 100)}%
          </p>
        </div>
        <button type="button" className="btn-ghost no-print" onClick={() => window.print()}>
          <Icon name="print" /> Print plan
        </button>
      </div>

      {/* Week at a glance: one column per day, a coloured dot per item. */}
      <nav aria-label="Week overview" className="card mt-5 grid max-w-3xl grid-cols-7 gap-1 p-2 sm:gap-2 sm:p-3">
        {DAYS.map((d) => {
          const items = byDay(d);
          return (
            <a key={d} href={`#day-${d}`} className="rounded-2xl px-1 py-2 text-center transition hover:bg-sand">
              <span className="block text-[11px] font-semibold uppercase tracking-wide text-ink/70">Day</span>
              <span className="block font-display text-xl font-semibold">{d}</span>
              <span className="mt-1 flex min-h-[10px] flex-wrap justify-center gap-1">
                {items.map((i) => (
                  <span key={i.candidate.id} title={`${categoryStyle(i.candidate.category).label}: ${i.candidate.name}`} className={`h-2.5 w-2.5 rounded-full ${categoryStyle(i.candidate.category).bar}`} />
                ))}
                {!items.length && <span className="text-[10px] text-ink/70">free</span>}
              </span>
            </a>
          );
        })}
      </nav>
      <ul className="mt-2 flex flex-wrap gap-3 text-xs text-ink/70" aria-label="Colour key">
        {Object.entries(CATEGORY).filter(([k]) => used.has(k as never)).map(([k, s]) => (
          <li key={k} className="inline-flex items-center gap-1.5"><span className={`h-2.5 w-2.5 rounded-full ${s.bar}`} />{s.label}</li>
        ))}
      </ul>

      <ul className="mt-3 space-y-0.5 text-xs text-ink/70">{plan.notes.map((n) => <li key={n}>{n}</li>)}</ul>

      {changes.length > 0 && (
        <div className="mt-4 rounded-2xl border border-clay-700/30 bg-clay-100/70 p-4" aria-live="polite">
          <h2 className="font-sans text-sm font-semibold text-clay-700">What changed</h2>
          <ul className="mt-1 list-disc space-y-0.5 pl-4 text-sm">{changes.map((c, i) => <li key={i}>{c}</li>)}</ul>
        </div>
      )}

      <ol className="relative mt-6 max-w-3xl space-y-5 before:absolute before:bottom-4 before:left-[19px] before:top-4 before:w-0.5 before:bg-ink/10">
        {DAYS.map((d) => {
          const items = byDay(d);
          return (
            <li key={d} id={`day-${d}`} className="relative scroll-mt-24 pl-14" aria-label={`Day ${d}`}>
              <span className={`absolute left-0 top-1 grid h-10 w-10 place-items-center rounded-full font-display text-lg font-semibold ${items.length ? "bg-teal-700 text-white" : "border border-ink/20 bg-paper text-ink/70"}`}>
                {d}
              </span>
              {items.length === 0 ? (
                <p className="pt-2.5 text-sm text-ink/70">Day {d} · Free day. Rest, or explore on your own.</p>
              ) : (
                <div className="grid gap-3">
                  {items.map((i) => {
                    const isSel = selected === i.candidate.id;
                    return (
                      <BridgeCard
                        key={i.candidate.id}
                        c={i.candidate}
                        ex={i}
                        highlight={changedIds.includes(i.candidate.id)}
                        eyebrow={<p className="mt-1.5 text-xs font-semibold capitalize text-ink/70">Day {d} · {i.slot}</p>}
                        footer={
                          <button
                            type="button"
                            aria-pressed={isSel}
                            className={`no-print rounded-full px-3 py-1 text-xs font-semibold ${isSel ? "bg-clay-700 text-white" : "border border-ink/20 text-ink/80 hover:bg-sand"}`}
                            onClick={() => setSelected(isSel ? null : i.candidate.id)}
                          >
                            {isSel ? "Selected ✓" : "Select"}
                          </button>
                        }
                      />
                    );
                  })}
                </div>
              )}
            </li>
          );
        })}
      </ol>

      <FeedbackBar
        busy={busy}
        familiarity={profile.familiarity}
        comfort={profile.comfort}
        selectedName={selectedName}
        onAction={(a) => {
          onFeedback(a, feedbackTarget(a, selected));
          setSelected(null);
        }}
      />
    </div>
  );
}

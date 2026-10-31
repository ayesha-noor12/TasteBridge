import type { ReactNode } from "react";
import type { CompareResponse } from "../types";
import { Icon, type IconName } from "../components/Icon";
import { SourceBadge } from "../components/SourceBadge";
import { categoryStyle } from "../lib/categories";

interface Props {
  data: CompareResponse;
  llmOn: boolean;
  busy: boolean;
  onRetry: () => void;
}

function Verdict({ tone, children }: { tone: "warn" | "good"; children: ReactNode }) {
  return (
    <p className={`mt-4 flex items-start gap-2 rounded-2xl px-3 py-2 text-sm font-medium ${tone === "good" ? "bg-teal-100 text-teal-800" : "bg-amber-100 text-amber-800"}`}>
      <Icon name={tone === "good" ? "check" : "alert"} className="mt-0.5 h-4 w-4 shrink-0" />
      <span>{children}</span>
    </p>
  );
}

export function Compare({ data, llmOn, busy, onRetry }: Props) {
  const b = data.baseline;
  const items = data.tastebridge;
  const fromQloo = items.filter((i) => i.candidate.source === "qloo").length;
  const toCheck = items.filter((i) => i.candidate.source === "unverified").length;

  return (
    <div className="space-y-5">
      <div>
        <p className="eyebrow">Side by side</p>
        <h1 className="font-display text-3xl font-semibold sm:text-4xl">A chatbot&apos;s guess vs. TasteBridge</h1>
        <p className="mt-1 text-sm text-ink/70">Same profile. Only one side uses Qloo data and checks your limits.</p>
      </div>
      <div className="grid gap-5 md:grid-cols-2">
        <section className="panel flex flex-col" aria-labelledby="col-llm">
          <h2 id="col-llm" className="flex items-center gap-2 font-display text-xl font-semibold">
            <span className="grid h-8 w-8 place-items-center rounded-full bg-amber-100 text-amber-800"><Icon name="chat" className="h-4 w-4" /></span>
            Language model only
          </h2>
          <p className="mb-4 mt-1 text-sm text-ink/70">No Qloo data, no budget, travel or diet checks.</p>
          {!b.available ? (
            <div className="flex flex-1 flex-col items-center justify-center rounded-2xl border border-dashed border-ink/20 p-6 text-center">
              <Icon name="chat" className="h-8 w-8 text-ink/70" />
              <p className="mt-2 font-semibold">{llmOn ? "The language model did not answer this time." : "The language model is switched off."}</p>
              <p className="mt-1 max-w-sm text-sm text-ink/70">{b.message ?? "Baseline unavailable."}</p>
              {llmOn && (
                <button type="button" className="btn-ghost mt-4" disabled={busy} onClick={onRetry}>
                  <Icon name="refresh" /> {busy ? "Trying…" : "Try again"}
                </button>
              )}
            </div>
          ) : (
            <>
              <span className="pill mb-3 self-start border border-dashed border-clay-700/50 bg-white text-clay-700"><Icon name="alert" className="h-3 w-3" />{b.label}</span>
              <ul className="space-y-2">
                {b.suggestions.map((s, i) => (
                  <li key={i} className="rounded-2xl bg-cream/70 p-3 text-sm"><strong>{s.name}</strong> <span className="text-ink/80">{s.description}</span></li>
                ))}
              </ul>
              {b.raw_text && <pre className="whitespace-pre-wrap rounded-2xl bg-cream/70 p-3 text-sm">{b.raw_text}</pre>}
            </>
          )}
          <Verdict tone="warn">
            {b.available
              ? `${b.suggestions.length ? `${b.suggestions.length} suggestions` : "Its answer"}, not checked against Qloo or your budget, travel and diet. Verify before going.`
              : "Nothing to judge yet: no suggestions were returned, and none are faked here."}
          </Verdict>
        </section>

        <section className="panel flex flex-col ring-1 ring-teal-700/20" aria-labelledby="col-tb">
          <h2 id="col-tb" className="flex items-center gap-2 font-display text-xl font-semibold">
            <span className="grid h-8 w-8 place-items-center rounded-full bg-teal-100 text-teal-800"><Icon name="spark" className="h-4 w-4" /></span>
            TasteBridge (Qloo)
          </h2>
          <p className="mb-4 mt-1 text-sm text-ink/70">
            {data.resolver.resolved.length} inputs matched in Qloo; budget, travel, diet and comfort applied in code.
          </p>
          <ol className="space-y-2">
            {items.map((i) => (
              <li key={i.candidate.id} className={`flex gap-3 rounded-2xl border-l-4 bg-cream/70 p-3 text-sm ${categoryStyle(i.candidate.category).border}`}>
                <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-teal-700 font-display font-semibold text-white" aria-label={`Day ${i.day}`}>{i.day}</span>
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <Icon name={i.candidate.category as IconName} className="h-3.5 w-3.5 text-ink/70" />
                    <span className="font-semibold">{i.candidate.name}</span>
                    <SourceBadge source={i.candidate.source} />
                  </div>
                  <p className="mt-0.5 text-ink/70">{i.why_this}</p>
                </div>
              </li>
            ))}
          </ol>
          <Verdict tone="good">
            {fromQloo} of {items.length} items are backed by Qloo evidence{toCheck ? `; ${toCheck} still need checking` : ""}. Your limits were applied in code; unknown costs are flagged, never assumed.
          </Verdict>
        </section>
      </div>
    </div>
  );
}

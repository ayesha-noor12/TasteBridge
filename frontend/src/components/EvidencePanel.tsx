import type { Candidate, Explained } from "../types";

export function EvidencePanel({ c, ex }: { c: Candidate; ex: Explained }) {
  const ev = c.evidence;
  return (
    <div className="mt-3 space-y-2 rounded-2xl border border-ink/10 bg-cream/70 p-4 text-sm">
      <p className="text-[11px] font-bold uppercase tracking-wider text-ink/70">
        Explanation: {ex.explanation_source === "ai" ? "AI-written from the evidence below" : "template"}
      </p>
      <p><strong>Why this:</strong> {ex.why_this}</p>
      <p><strong>Why here:</strong> {ex.why_here}</p>
      <p><strong>Why now:</strong> {ex.why_now}</p>
      <dl className="grid grid-cols-[auto,1fr] gap-x-3 gap-y-1 border-t border-ink/10 pt-2 text-xs">
        <dt className="font-semibold">Your inputs</dt>
        <dd>{ev.seed_inputs.length ? ev.seed_inputs.join("; ") : "None (not a Qloo result)"}</dd>
        <dt className="font-semibold">Qloo match</dt>
        <dd>{ev.qloo_entity ?? "No Qloo match"}</dd>
        <dt className="font-semibold">Qloo signal</dt>
        <dd>{ev.qloo_signal ?? "None returned"}</dd>
        <dt className="font-semibold">City signal</dt>
        <dd>{ev.city_signal}</dd>
        <dt className="font-semibold">Verified on</dt>
        <dd>{c.verified_on ?? "Not verified"}</dd>
        {c.url && (
          <>
            <dt className="font-semibold">Link</dt>
            <dd className="break-all"><a className="text-teal-700 underline" href={c.url} target="_blank" rel="noopener noreferrer">{c.url}</a></dd>
          </>
        )}
      </dl>
      {ev.raw && (
        <details>
          <summary className="cursor-pointer text-xs text-ink/70">Raw Qloo data (truncated)</summary>
          <pre className="mt-1 max-h-48 overflow-auto whitespace-pre-wrap break-all text-xs">{JSON.stringify(ev.raw, null, 2)}</pre>
        </details>
      )}
    </div>
  );
}

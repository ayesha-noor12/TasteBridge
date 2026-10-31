import type { Cohort } from "../types";

export function Admin({ data }: { data: Cohort }) {
  const max = Math.max(1, ...data.clusters.map((c) => c.count));
  return (
    <div className="space-y-5">
      <div>
        <p className="text-xs font-semibold uppercase tracking-widest text-clay-700">For student offices</p>
        <h2 className="font-display text-3xl font-semibold">Cohort taste clusters</h2>
      </div>
      <section className="panel">
        <div className="flex flex-wrap items-center gap-2">
          <span className="pill border border-clay-700/30 bg-clay-100 text-clay-700">Synthetic demo data</span>
          <p className="text-sm text-ink/70">{data.cohort}. For international-student offices deciding what to host. Not real students.</p>
        </div>
        <ul className="mt-5 space-y-4">
          {data.clusters.map((c) => (
            <li key={c.label}>
              <div className="flex justify-between text-sm"><span className="font-medium">{c.label}</span><span className="text-ink/70">{c.count} students</span></div>
              <div className="mt-1 h-3 w-full rounded-full bg-sand" role="img" aria-label={`${c.label}: ${c.count}`}>
                <div className="h-3 rounded-full bg-teal-700" style={{ width: `${(c.count / max) * 100}%` }} />
              </div>
              <p className="mt-1 text-xs text-ink/70">Idea: {c.suggested_event}</p>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}

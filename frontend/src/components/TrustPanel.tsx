import { Icon, type IconName } from "./Icon";

// Each statement is checked against the code: resolver.py / candidates.py (Qloo), explain.py and
// baseline.py (language model), sessions.py and qloo_adapter.py (what is kept).
const COLUMNS: { icon: IconName; title: string; points: string[] }[] = [
  {
    icon: "search",
    title: "What Qloo sees",
    points: [
      "Each loved item you type, sent as a search.",
      "Then only the matched Qloo entity IDs, plus the city (Toronto) for places.",
      "Never your origin, budget, diet or comfort settings.",
    ],
  },
  {
    icon: "chat",
    title: "What the language model sees",
    points: [
      "Only if it is switched on (it is optional).",
      "For explanations: each card's evidence, your loved items and what you chose to keep.",
      "On the Compare page: your whole profile, including origin, so it can make its own guess.",
    ],
  },
  {
    icon: "lock",
    title: "What is kept, and where",
    points: [
      "Your profile lives in server memory for this session only: no account, no database.",
      "It is deleted when you press Reset, after 2 hours idle, or when the server restarts.",
      "Qloo's answers are cached on the server so repeat searches are not re-sent.",
    ],
  },
];

export function TrustPanel() {
  return (
    <section aria-labelledby="trust-title" className="panel">
      <h2 id="trust-title" className="font-display text-xl font-semibold">Where your answers go</h2>
      <div className="mt-4 grid gap-5 md:grid-cols-3">
        {COLUMNS.map((c) => (
          <div key={c.title}>
            <h3 className="flex items-center gap-2 font-sans text-sm font-semibold">
              <span className="grid h-8 w-8 place-items-center rounded-full bg-teal-100 text-teal-800"><Icon name={c.icon} className="h-4 w-4" /></span>
              {c.title}
            </h3>
            <ul className="mt-2 space-y-1.5 text-sm text-ink/80">
              {c.points.map((p) => (
                <li key={p} className="flex gap-2"><span aria-hidden="true" className="mt-2 h-1 w-1 shrink-0 rounded-full bg-ink/70" />{p}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </section>
  );
}

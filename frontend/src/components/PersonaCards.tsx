import type { Profile } from "../types";
import { PERSONAS } from "../lib/personas";
import { Illustration } from "./Art";
import { Icon } from "./Icon";

export function PersonaCards({ busy, onPick }: { busy: boolean; onPick: (p: Profile) => void }) {
  return (
    <section aria-labelledby="personas-title">
      <p className="eyebrow">One-tap scenarios</p>
      <h2 id="personas-title" className="font-display text-3xl font-semibold">Or plan a week for one of these students</h2>
      <p className="mt-1 text-sm text-ink/75">Invented examples. Their answers go through the real pipeline; nothing on the next page is pre-made.</p>
      <div className="mt-5 grid gap-4 md:grid-cols-3">
        {PERSONAS.map((p) => (
          <article key={p.name} className="card card-hover flex flex-col overflow-hidden">
            <Illustration src={p.img} alt="" icon="social" tint="bg-peach" className="h-28 w-full" />
            <div className="flex flex-1 flex-col p-5">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <h3 className="font-display text-xl font-semibold">{p.name}</h3>
                  <p className="text-sm text-ink/70">From {p.profile.origin} · ${p.profile.budget_per_activity_cad} CAD per activity</p>
                </div>
                <span className="pill shrink-0 border border-amber-800/30 bg-amber-100 text-amber-800">Invented example</span>
              </div>
              <p className="mt-2 text-sm text-ink/80">{p.blurb}</p>
              <ul className="mt-3 flex flex-wrap gap-1.5" aria-label={`${p.name} loves`}>
                {p.profile.loved_items.map((i) => (
                  <li key={i.text} className="chip">{i.text} <span className="text-ink/70">· {i.type}</span></li>
                ))}
              </ul>
              <button type="button" className="btn-primary mt-auto self-start" style={{ marginTop: "1.25rem" }} disabled={busy} onClick={() => onPick(p.profile)}>
                Plan {p.name}&apos;s week <Icon name="arrow" />
              </button>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

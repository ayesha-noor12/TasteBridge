import { Icon, type IconName } from "./Icon";

const STEPS: { icon: IconName; title: string; body: string }[] = [
  { icon: "home", title: "Tell us what you love", body: "A few dishes, artists, shows or places from home. You choose; we never guess from where you are from." },
  { icon: "spark", title: "Qloo finds the taste links", body: "Qloo matches your favourites and suggests related places in Toronto and related artists, with evidence on every card." },
  { icon: "calendar", title: "Get a week that fits", body: "Your budget, travel time and diet are applied in code, then we build a 7-day plan you can adjust in one tap." },
];

export function HowItWorks() {
  return (
    <section aria-labelledby="how-title">
      <p className="eyebrow">How it works</p>
      <h2 id="how-title" className="font-display text-3xl font-semibold">Three steps, about a minute</h2>
      <ol className="mt-5 grid gap-4 md:grid-cols-3">
        {STEPS.map((s, i) => (
          <li key={s.title} className="panel card-hover">
            <div className="flex items-center gap-3">
              <span className="grid h-11 w-11 place-items-center rounded-2xl bg-peach text-clay-700"><Icon name={s.icon} className="h-5 w-5" /></span>
              <span aria-hidden="true" className="font-display text-3xl font-semibold text-ink/20">{i + 1}</span>
            </div>
            <h3 className="mt-3 font-display text-lg font-semibold">{s.title}</h3>
            <p className="mt-1 text-sm leading-relaxed text-ink/75">{s.body}</p>
          </li>
        ))}
      </ol>
    </section>
  );
}

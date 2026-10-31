import { useState } from "react";
import type { ItemType, Presets, Profile } from "../types";
import type { ReactNode } from "react";
import { Illustration } from "../components/Art";
import { HowItWorks } from "../components/HowItWorks";
import { PersonaCards } from "../components/PersonaCards";
import { TrustPanel } from "../components/TrustPanel";
import { Chips } from "../components/Chips";
import { Icon } from "../components/Icon";

interface Props {
  presets: Presets;
  initial: Profile;
  busy: boolean;
  error: string | null;
  onSubmit: (p: Profile) => void;
}

function Step({ n, title, hint, children }: { n: number; title: string; hint?: string; children: ReactNode }) {
  return (
    <section className="panel">
      <div className="mb-4 flex items-start gap-3">
        <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-teal-700 font-display font-semibold text-white">{n}</span>
        <div>
          <h3 className="font-display text-xl font-semibold leading-tight">{title}</h3>
          {hint && <p className="mt-0.5 text-sm text-ink/70">{hint}</p>}
        </div>
      </div>
      <div className="space-y-4">{children}</div>
    </section>
  );
}

export function Onboarding({ presets, initial, busy, error, onSubmit }: Props) {
  const [p, setP] = useState<Profile>(initial);
  const set = <K extends keyof Profile>(k: K, v: Profile[K]) => setP((old) => ({ ...old, [k]: v }));
  const max = presets.limits.max_loved_items;

  const toggle = (list: string[], v: string) => (list.includes(v) ? list.filter((x) => x !== v) : [...list, v]);
  const toggleDiet = (d: string) => {
    if (d === "none") return set("diet", ["none"]);
    const next = toggle(p.diet.filter((x) => x !== "none"), d);
    set("diet", next.length ? next : ["none"]);
  };
  const updateItem = (i: number, patch: Partial<{ text: string; type: ItemType }>) =>
    set("loved_items", p.loved_items.map((it, j) => (j === i ? { ...it, ...patch } : it)));

  const cleaned = { ...p, loved_items: p.loved_items.filter((i) => i.text.trim()) };

  return (
    <div className="space-y-12">
      <section className="card relative overflow-hidden animate-rise">
        <div className="grid items-center gap-8 p-6 sm:p-10 lg:grid-cols-[1.1fr,1fr]">
          <div>
            <p className="eyebrow">Welcome to Toronto</p>
            <h1 className="mt-3 font-display text-4xl font-semibold leading-[1.08] sm:text-5xl lg:text-[3.4rem]">
              Your taste from home, matched to <span className="text-clay-700">your new city.</span>
            </h1>
            <p className="mt-4 max-w-lg text-base leading-relaxed text-ink/80">
              TasteBridge helps international students use Qloo&apos;s taste data to turn the food, music and shows they love into things they can actually do this week.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <button type="button" className="btn-primary px-6 py-3 text-base" disabled={busy} onClick={() => onSubmit(presets.demo_profile)}>
                {busy ? "Asking Qloo…" : "Try the demo student"} <Icon name="arrow" />
              </button>
              <a href="#profile-form" className="btn-ghost px-6 py-3 text-base">Build my own</a>
            </div>
            <p className="mt-4 text-xs text-ink/70">The demo student is invented. Their week is built live from Qloo, nothing is pre-made.</p>
          </div>
          <Illustration
            src="/img/hero.svg"
            alt="Illustration of the Toronto skyline at sunset, with tea and food on a table"
            icon="food"
            tint="bg-peach"
            eager
            className="aspect-[16/11] w-full rounded-[28px]"
          />
        </div>
      </section>

      <PersonaCards busy={busy} onPick={onSubmit} />

      <HowItWorks />

    <form
      id="profile-form"
      className="scroll-mt-24 space-y-6"
      aria-labelledby="form-title"
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit(cleaned);
      }}
    >
      <div>
        <p className="eyebrow">Build my own</p>
        <h2 id="form-title" className="font-display text-3xl font-semibold">Tell us about you</h2>
      </div>
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-teal-700/20 bg-teal-100/60 px-4 py-3">
        <p className="text-sm">
          <strong>You choose what matters; we do not guess your identity.</strong>{" "}
          <span className="text-ink/80">Nothing is inferred from where you are from.</span>
        </p>
        <button type="button" className="text-sm font-semibold text-teal-700 hover:underline" onClick={() => setP(presets.demo_profile)}>
          Fill in the demo profile
        </button>
      </div>

      <Step n={1} title="About you" hint="Where you are coming from, and what you want to keep.">
        <div>
          <label htmlFor="origin" className="label">Where are you coming from?</label>
          <input id="origin" className="input" maxLength={60} required value={p.origin} onChange={(e) => set("origin", e.target.value)} />
        </div>
        <div>
          <span className="label">Moving to</span>
          <p className="font-medium">{p.destination_city} <span className="text-sm font-normal text-ink/70">(the only demo city)</span></p>
        </div>
        <div>
          <span className="label">What do you want to keep from home?</span>
          <Chips label="What to keep" options={presets.preserve_chips} selected={p.preserve} onToggle={(v) => set("preserve", toggle(p.preserve, v))} />
        </div>
      </Step>

      <Step
        n={2}
        title="Things you love"
        hint="Use specific names (an artist, a dish, a show), not descriptions. We look these up in Qloo; anything it cannot find is listed, not guessed."
      >
        {p.loved_items.map((it, i) => (
          <div key={i} className="flex flex-wrap gap-2 sm:flex-nowrap">
            <input
              aria-label={`Loved item ${i + 1}`}
              className="input"
              maxLength={presets.limits.max_text_len}
              placeholder="e.g. Taylor Swift, Pad Thai, Friends"
              value={it.text}
              onChange={(e) => updateItem(i, { text: e.target.value })}
            />
            <select aria-label={`Type of item ${i + 1}`} className="input sm:w-36" value={it.type} onChange={(e) => updateItem(i, { type: e.target.value as ItemType })}>
              {presets.item_types.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
            <button type="button" className="btn-ghost" onClick={() => set("loved_items", p.loved_items.filter((_, j) => j !== i))} aria-label={`Remove item ${i + 1}`}>
              Remove
            </button>
          </div>
        ))}
        <div className="flex flex-wrap gap-2">
          <button type="button" className="btn-ghost" disabled={p.loved_items.length >= max} onClick={() => set("loved_items", [...p.loved_items, { text: "", type: "dish" }])}>
            Add item
          </button>
          <button type="button" className="btn-ghost" onClick={() => set("loved_items", [])}>
            Skip (no items)
          </button>
        </div>
        <div>
          <span className="text-sm text-ink/70">Examples: </span>
          {presets.example_items.map((ex) => (
            <button
              key={ex.text}
              type="button"
              className="m-1 rounded-full border border-dashed border-ink/25 bg-white px-3 py-1 text-sm hover:border-teal-700 hover:text-teal-700"
              disabled={p.loved_items.length >= max || p.loved_items.some((i) => i.text === ex.text)}
              onClick={() => set("loved_items", [...p.loved_items, ex])}
            >
              + {ex.text}
            </button>
          ))}
        </div>
      </Step>

      <Step n={3} title="Your week" hint="Hard limits. Anything outside them is set aside, and we tell you why.">
        <div className="grid gap-5 sm:grid-cols-3">
        <div>
          <label htmlFor="budget" className="label">Budget per activity: ${p.budget_per_activity_cad} CAD</label>
          <input id="budget" type="range" min={0} max={200} step={5} className="range" value={p.budget_per_activity_cad} onChange={(e) => set("budget_per_activity_cad", Number(e.target.value))} />
        </div>
        <div>
          <label htmlFor="hours" className="label">Free hours per week: {p.hours_per_week}</label>
          <input id="hours" type="range" min={1} max={40} className="range" value={p.hours_per_week} onChange={(e) => set("hours_per_week", Number(e.target.value))} />
        </div>
        <div>
          <label htmlFor="travel" className="label">Max travel: {p.max_travel_minutes} min</label>
          <input id="travel" type="range" min={5} max={120} step={5} className="range" value={p.max_travel_minutes} onChange={(e) => set("max_travel_minutes", Number(e.target.value))} />
        </div>
        </div>
      </Step>

      <Step n={4} title="Food and company">
        <div className="grid gap-5 sm:grid-cols-2">
        <div>
          <span className="label">Diet</span>
          <Chips label="Diet" options={presets.diets} selected={p.diet} onToggle={toggleDiet} />
        </div>
        <fieldset>
          <legend className="label">Going out</legend>
          {presets.comfort_levels.map((c) => (
            <label key={c} className="mr-4 mt-1 inline-flex items-center gap-2 text-sm">
              <input type="radio" name="comfort" className="accent-teal-700" checked={p.comfort === c} onChange={() => set("comfort", c)} />
              {c === "solo_ok" ? "Fine going alone" : c === "small_group" ? "Small groups" : "Prefer going with a friend"}
            </label>
          ))}
        </fieldset>
        </div>
      </Step>

      {error && <p role="alert" className="rounded-lg border border-clay-700 bg-clay-100 p-3 text-clay-700">{error}</p>}
      <div className="flex flex-wrap items-center gap-3">
        <button type="submit" className="btn-primary px-7 py-3 text-base" disabled={busy || !p.origin.trim()}>
          {busy ? "Asking Qloo…" : "Build my bridge"} <Icon name="arrow" />
        </button>
        {!p.origin.trim() && <span className="text-sm text-ink/70">Tell us where you are coming from to continue.</span>}
      </div>
    </form>

      <TrustPanel />
    </div>
  );
}

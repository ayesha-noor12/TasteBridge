import { useState, type ReactNode } from "react";
import type { Candidate, Explained } from "../types";
import { categoryStyle } from "../lib/categories";
import { formatCad, formatMinutes, hoursToday, mapsLink } from "../lib/logic";
import { Thumb } from "./Art";
import { EvidencePanel } from "./EvidencePanel";
import { Icon, type IconName } from "./Icon";
import { ModeTag, SourceBadge } from "./SourceBadge";

interface Props {
  c: Candidate;
  ex: Explained;
  highlight?: boolean;
  leading?: boolean;
  eyebrow?: ReactNode;
  footer?: ReactNode;
}

export function BridgeCard({ c, ex, highlight, leading, eyebrow, footer }: Props) {
  const [open, setOpen] = useState(false);
  const cat = categoryStyle(c.category);
  const f = c.qloo_facts;
  const today = hoursToday(f?.hours);
  const map = mapsLink(c.name, c.address);
  return (
    <article
      className={`card card-hover animate-rise border-l-4 ${cat.border} p-4 ${highlight ? "ring-2 ring-clay-700" : ""} ${leading ? "ring-2 ring-gold/70" : ""}`}
    >
      <div className="flex gap-4">
        <Thumb category={c.category} photo={c.image_url} name={c.name} className="h-16 w-16 shrink-0 sm:h-20 sm:w-20" />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className={`pill ${cat.chip}`}>
              <Icon name={c.category as IconName} className="h-3 w-3" />
              {cat.label}
            </span>
            <ModeTag mode={c.mode} />
            <SourceBadge source={c.source} />
          </div>
          {eyebrow}
          {leading && <p className="mt-1.5 text-[11px] font-bold uppercase tracking-wider text-clay-700">★ Top pick right now</p>}
          {highlight && <p className="mt-1.5 text-[11px] font-bold uppercase tracking-wider text-clay-700">Changed</p>}
          <h4 className="mt-1.5 break-words font-display text-lg font-semibold leading-snug">{c.name}</h4>
          {(f?.genre || f?.neighborhood) && (
            <p className="mt-0.5 text-sm text-ink/70">{[f.genre, f.neighborhood].filter(Boolean).join(" · ")}</p>
          )}
        </div>
      </div>
      <div className="mt-3 flex flex-wrap gap-1.5">
        {f?.rating != null && (
          <span className="chip" title="Business rating as returned by Qloo"><span aria-hidden="true" className="text-gold">★</span>{f.rating.toFixed(1)}<span className="sr-only"> out of 5, rated</span></span>
        )}
        {f?.price_level != null ? (
          <span className="chip" title={`Qloo price level ${f.price_level} of 4. The exact cost is not verified.`}>
            <Icon name="wallet" className="h-3.5 w-3.5" />{"$".repeat(f.price_level)}<span aria-hidden="true" className="text-ink/40">{"$".repeat(4 - f.price_level)}</span>
            <span className="sr-only">price level {f.price_level} of 4</span>
          </span>
        ) : (
          <span className="chip"><Icon name="wallet" className="h-3.5 w-3.5" />{formatCad(c.cost_cad)}</span>
        )}
        {today ? (
          <span className="chip"><Icon name="clock" className="h-3.5 w-3.5" />{today}</span>
        ) : (
          c.travel_minutes != null || !f ? <span className="chip"><Icon name="clock" className="h-3.5 w-3.5" />{formatMinutes(c.travel_minutes)}</span> : null
        )}
        {c.social && <span className="chip"><Icon name="social" className="h-3.5 w-3.5" />Social</span>}
        {c.source === "curated" && c.verified_on && (
          <span className="chip" title="Checked against the official page linked below on this date"><Icon name="check" className="h-3.5 w-3.5" />Checked {c.verified_on}</span>
        )}
      </div>
      {c.address && (
        <p className="mt-1.5 flex items-start gap-1 text-xs text-ink/70"><Icon name="pin" className="mt-px h-3.5 w-3.5 shrink-0" />{c.address}</p>
      )}
      {f?.description && <p className="mt-2 text-sm italic leading-relaxed text-ink/75">“{f.description}”<span className="not-italic text-ink/70"> (Qloo)</span></p>}
      <p className="mt-3 text-sm leading-relaxed text-ink/80">{ex.why_this}</p>
      <div className="mt-2 flex items-start gap-2 rounded-2xl bg-peach px-3 py-2 text-sm text-ink/85">
        <Icon name="bulb" className="mt-0.5 h-4 w-4 shrink-0 text-clay-700" />
        <span>{ex.why_now}</span>
      </div>
      <div className="mt-2 flex flex-wrap items-center justify-between gap-2">
        <button type="button" className="inline-flex items-center gap-1 text-sm font-semibold text-teal-700 hover:underline" aria-expanded={open} onClick={() => setOpen(!open)}>
          {open ? "Hide evidence" : "Why this? Show evidence"}
          <Icon name="chevron" className={`h-4 w-4 transition ${open ? "rotate-180" : ""}`} />
        </button>
        <span className="flex flex-wrap items-center gap-3">
          {map && <a className="text-sm font-semibold text-teal-700 hover:underline" href={map} target="_blank" rel="noopener noreferrer">Directions<span className="sr-only"> to {c.name} (opens Google Maps)</span></a>}
          {c.url && <a className="text-sm font-semibold text-teal-700 hover:underline" href={c.url} target="_blank" rel="noopener noreferrer">Website<span className="sr-only"> of {c.name}</span></a>}
          {footer}
        </span>
      </div>
      {open && <EvidencePanel c={c} ex={ex} />}
    </article>
  );
}

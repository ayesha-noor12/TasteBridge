import { clampFamiliarity, sliderLabel } from "../lib/logic";

export function FamiliaritySlider({ value, onChange }: { value: number; onChange: (v: number) => void }) {
  return (
    <div>
      <label htmlFor="familiarity" className="label">
        How much like home? · <span className="normal-case tracking-normal text-ink">{sliderLabel(value)}</span>
      </label>
      <div className="flex items-center gap-3 text-sm font-medium">
        <span className="whitespace-nowrap text-clay-700">New in Toronto</span>
        <input
          id="familiarity"
          type="range"
          min={0}
          max={1}
          step={0.05}
          value={value}
          onChange={(e) => onChange(clampFamiliarity(Number(e.target.value)))}
          className="range"
          aria-valuetext={sliderLabel(value)}
        />
        <span className="whitespace-nowrap text-teal-700">Like home</span>
      </div>
      <p className="mt-1 text-xs font-semibold text-ink/80">
        <span className="text-teal-700">{Math.round(value * 100)}% taste of home</span> · <span className="text-clay-700">{100 - Math.round(value * 100)}% something new</span>
        <span className="font-normal text-ink/70"> (how the ranking leans, not a fixed split)</span>
      </p>
    </div>
  );
}

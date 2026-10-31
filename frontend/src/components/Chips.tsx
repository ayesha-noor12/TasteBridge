interface Props {
  options: string[];
  selected: string[];
  onToggle: (value: string) => void;
  label: string;
}

export function Chips({ options, selected, onToggle, label }: Props) {
  return (
    <div role="group" aria-label={label} className="flex flex-wrap gap-2">
      {options.map((o) => {
        const on = selected.includes(o);
        return (
          <button
            key={o}
            type="button"
            aria-pressed={on}
            onClick={() => onToggle(o)}
            className={`rounded-full border px-3.5 py-1.5 text-sm font-medium capitalize transition ${on ? "border-teal-700 bg-teal-700 text-white shadow-sm" : "border-ink/15 bg-white hover:border-teal-700/50"}`}
          >
            {on && "✓ "}
            {o.replace("_", " ")}
          </button>
        );
      })}
    </div>
  );
}

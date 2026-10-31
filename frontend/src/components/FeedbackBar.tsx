import type { FeedbackAction } from "../types";
import { FEEDBACK_BUTTONS, feedbackDisabled } from "../lib/logic";

interface Props {
  busy: boolean;
  familiarity: number;
  comfort: string;
  selectedName: string | null;
  onAction: (a: FeedbackAction) => void;
}

/** Sticky re-plan bar at the bottom of the plan page. */
export function FeedbackBar({ busy, familiarity, comfort, selectedName, onAction }: Props) {
  return (
    <div className="no-print sticky bottom-3 z-10 mt-6 max-w-3xl">
      <div className="card flex flex-col gap-3 border-ink/10 bg-paper/95 p-3 backdrop-blur sm:flex-row sm:items-center">
        <div className="min-w-0 px-1 sm:flex-1">
          <p className="text-sm font-semibold">Not quite right? Re-plan in one tap.</p>
          <p className="truncate text-xs text-ink/70">
            {selectedName ? `"Too expensive" will remove: ${selectedName}` : 'Tip: select an item first for "Too expensive".'}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {FEEDBACK_BUTTONS.map((b) => (
            <button
              key={b.action}
              type="button"
              className="btn-ghost px-4 py-2"
              title={b.hint}
              aria-describedby={`hint-${b.action}`}
              disabled={busy || feedbackDisabled(familiarity, b.action, comfort)}
              onClick={() => onAction(b.action)}
            >
              {b.label}
              <span id={`hint-${b.action}`} className="sr-only">{b.hint}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

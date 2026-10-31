import type { BannerKind } from "../lib/logic";
import { Icon, type IconName } from "./Icon";

const TEXT: Record<BannerKind, { title: string; body: string; cls: string; icon: IconName }> = {
  demo: {
    title: "Demo data, not from Qloo",
    body: "Mock mode: results are synthetic fixtures. Set QLOO_MODE=live with a Qloo key for real results.",
    cls: "bg-amber-100 text-amber-800 border-amber-800/40",
    icon: "alert",
  },
  qloo_down: {
    title: "Qloo unavailable",
    body: "The last Qloo request failed. Nothing from another source is shown as a Qloo result.",
    cls: "bg-clay-100 text-clay-700 border-clay-700/40",
    icon: "alert",
  },
  llm_off: {
    title: "Language model off",
    body: "Explanations use fixed templates over the evidence, and the LLM-only comparison is unavailable.",
    cls: "bg-paper text-ink/80 border-ink/10",
    icon: "chat",
  },
};

export function Banner({ kinds }: { kinds: BannerKind[] }) {
  if (!kinds.length) return null;
  return (
    <div className="no-print flex flex-col gap-2" role="status">
      {kinds.map((k) => (
        <div key={k} className={`flex items-start gap-2.5 rounded-2xl border px-4 py-2.5 text-sm ${TEXT[k].cls}`}>
          <Icon name={TEXT[k].icon} className="mt-0.5 h-4 w-4 shrink-0" />
          <p>
            <strong className={k === "demo" ? "mr-1 rounded-full bg-amber-800 px-2 py-0.5 text-xs uppercase tracking-wide text-amber-100" : ""}>{TEXT[k].title}</strong>
            {k === "demo" ? " " : ". "}
            {TEXT[k].body}
          </p>
        </div>
      ))}
    </div>
  );
}

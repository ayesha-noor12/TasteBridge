import { badgeFor } from "../lib/logic";
import { Icon, type IconName } from "./Icon";

// Each source has its own color AND its own icon + text, so it never relies on color alone.
const ICON: Record<string, IconName> = { qloo: "spark", curated: "check", unverified: "alert" };

export function SourceBadge({ source }: { source: string }) {
  const b = badgeFor(source);
  return (
    <span title={b.title} className={`pill border ${b.className}`}>
      <Icon name={ICON[source] ?? "alert"} className="h-3 w-3" />
      {b.label}
    </span>
  );
}

export function ModeTag({ mode }: { mode: string }) {
  const familiar = mode === "familiar";
  return (
    <span className={`pill ${familiar ? "bg-teal-700 text-white" : "bg-clay-700 text-white"}`}>
      <Icon name={familiar ? "home" : "compass"} className="h-3 w-3" />
      {familiar ? "Familiar" : "Discover"}
    </span>
  );
}

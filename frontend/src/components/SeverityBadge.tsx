const STYLES: Record<string, string> = {
  critical: "bg-red-500/15 text-red-400 border-red-500/30",
  high: "bg-orange-500/15 text-orange-400 border-orange-500/30",
  medium: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  low: "bg-sky-500/15 text-sky-400 border-sky-500/30",
};

const DOT: Record<string, string> = {
  critical: "🔴",
  high: "🟠",
  medium: "🟡",
  low: "🔵",
};

export default function SeverityBadge({ severity }: { severity: string }) {
  const key = severity?.toLowerCase() || "low";
  return (
    <span
      className={`inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-full border ${
        STYLES[key] || STYLES.low
      }`}
    >
      <span>{DOT[key] || "🔵"}</span>
      {severity?.toUpperCase()}
    </span>
  );
}

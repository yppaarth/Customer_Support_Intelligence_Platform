export function Badge({ children, tone = "neutral" }: { children: React.ReactNode; tone?: "neutral" | "good" | "warn" | "bad" }) {
  const cls = {
    neutral: "border-line bg-white text-ink",
    good: "border-teal/30 bg-teal/10 text-teal",
    warn: "border-amber/30 bg-amber/10 text-amber",
    bad: "border-rose/30 bg-rose/10 text-rose"
  }[tone];
  return <span className={`inline-flex items-center rounded border px-2 py-0.5 text-xs font-medium ${cls}`}>{children}</span>;
}

import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";

export function EvaluationsPage() {
  const q = useQuery({ queryKey: ["evaluation-latest"], queryFn: () => api<any>("/evaluations/latest") });
  return (
    <section>
      <h1 className="text-2xl font-semibold">Evaluation Runs</h1>
      <div className="mt-4 grid gap-3 md:grid-cols-4">
        {["total_cases", "classification_accuracy", "escalation_accuracy", "estimated_cost_per_ticket_usd"].map((key) => <div key={key} className="rounded border border-line bg-panel p-4"><div className="text-sm text-slate-500">{key.replaceAll("_", " ")}</div><div className="mt-2 text-2xl font-semibold">{q.data?.[key] ?? "-"}</div></div>)}
      </div>
      <div className="mt-4 rounded border border-line bg-panel p-4 text-sm">
        Run with <code>make eval</code>. Latest report status: <strong>{q.data?.status ?? "loaded"}</strong>.
      </div>
    </section>
  );
}

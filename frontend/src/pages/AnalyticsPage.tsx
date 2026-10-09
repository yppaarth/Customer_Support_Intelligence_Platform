import { useQuery } from "@tanstack/react-query";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../lib/api";

export function AnalyticsPage() {
  const q = useQuery({ queryKey: ["analytics"], queryFn: () => api<any>("/analytics") });
  const data = q.data;
  return (
    <section>
      <h1 className="text-2xl font-semibold">Analytics</h1>
      <p className="text-sm text-slate-500">Metrics are derived from persisted demo records and labeled as estimates where appropriate.</p>
      <div className="mt-4 grid gap-3 md:grid-cols-4">
        {["total_tickets", "open_tickets", "resolved_tickets", "estimated_total_ai_cost_usd"].map((key) => <div key={key} className="rounded border border-line bg-panel p-4"><div className="text-sm text-slate-500">{key.replaceAll("_", " ")}</div><div className="mt-2 text-2xl font-semibold">{data?.[key] ?? "-"}</div></div>)}
      </div>
      <div className="mt-4 h-80 rounded border border-line bg-panel p-4">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data?.tickets_by_status ?? []}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="status" /><YAxis allowDecimals={false} /><Tooltip /><Bar dataKey="count" fill="#0f766e" /></BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}

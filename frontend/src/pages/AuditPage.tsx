import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";

export function AuditPage() {
  const q = useQuery({ queryKey: ["audit"], queryFn: () => api<Array<{ action: string; resource_type: string; resource_id: string | null; created_at: string }>>("/audit") });
  return (
    <section>
      <h1 className="text-2xl font-semibold">Audit Log</h1>
      <div className="mt-4 overflow-hidden rounded border border-line bg-panel">
        <table className="w-full text-left text-sm">
          <thead className="bg-mist text-xs uppercase text-slate-500"><tr><th className="p-3">Action</th><th>Resource</th><th>Time</th></tr></thead>
          <tbody>{q.data?.map((row, index) => <tr key={`${row.created_at}-${index}`} className="border-t border-line"><td className="p-3 font-medium">{row.action}</td><td>{row.resource_type} {row.resource_id}</td><td>{new Date(row.created_at).toLocaleString()}</td></tr>)}</tbody>
        </table>
      </div>
    </section>
  );
}

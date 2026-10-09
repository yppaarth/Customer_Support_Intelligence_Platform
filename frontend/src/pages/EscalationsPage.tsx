import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Badge } from "../components/Badge";
import { api } from "../lib/api";

export function EscalationsPage() {
  const q = useQuery({ queryKey: ["escalations"], queryFn: () => api<Array<{ id: string; ticket_id: string; reason: string; priority: string; status: string }>>("/escalations") });
  return <section><h1 className="text-2xl font-semibold">Escalation Queue</h1><div className="mt-4 space-y-3">{q.data?.map((e) => <div key={e.id} className="rounded border border-line bg-panel p-4"><Link className="font-medium text-teal" to={`/tickets/${e.ticket_id}`}>{e.ticket_id}</Link><p className="mt-2 text-sm">{e.reason}</p><div className="mt-2 flex gap-2"><Badge tone="bad">{e.priority}</Badge><Badge>{e.status}</Badge></div></div>)}</div></section>;
}

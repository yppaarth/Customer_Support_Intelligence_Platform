import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Search } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { Badge } from "../components/Badge";
import { api } from "../lib/api";
import type { Page, TicketListItem } from "../types/api";

export function TicketsPage() {
  const qc = useQueryClient();
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [message, setMessage] = useState("My order is delayed and tracking has not moved for six days.");
  const tickets = useQuery({
    queryKey: ["tickets", search, status],
    queryFn: () => api<Page<TicketListItem>>(`/tickets?search=${encodeURIComponent(search)}&status=${encodeURIComponent(status)}`)
  });
  const create = useMutation({
    mutationFn: () => api<{ id: string }>("/tickets", { method: "POST", body: JSON.stringify({ subject: "Manual support request", customer_email: "new.customer@example.test", customer_name: "New Customer", message }) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tickets"] })
  });

  return (
    <section>
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Support Inbox</h1>
          <p className="text-sm text-slate-500">Persisted tickets, classifications, confidence, and escalation state.</p>
        </div>
        <button className="focus-ring inline-flex items-center gap-2 rounded bg-teal px-3 py-2 text-sm font-medium text-white" onClick={() => create.mutate()}>
          <Plus size={16} /> Create ticket
        </button>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-[1fr_180px]">
        <label className="relative">
          <Search className="absolute left-3 top-2.5 text-slate-400" size={18} />
          <input className="focus-ring w-full rounded border border-line py-2 pl-10 pr-3" placeholder="Search tickets" value={search} onChange={(e) => setSearch(e.target.value)} />
        </label>
        <select className="focus-ring rounded border border-line px-3 py-2" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All statuses</option>
          <option value="escalated">Escalated</option>
          <option value="waiting_for_human_review">Human review</option>
          <option value="resolved">Resolved</option>
        </select>
      </div>
      <textarea className="focus-ring mt-3 h-20 w-full rounded border border-line p-3 text-sm" value={message} onChange={(e) => setMessage(e.target.value)} />
      <div className="mt-4 overflow-hidden rounded border border-line bg-panel">
        <table className="w-full text-left text-sm">
          <thead className="bg-mist text-xs uppercase text-slate-500"><tr><th className="p-3">Ticket</th><th>Status</th><th>Priority</th><th>Category</th><th>Confidence</th><th>Customer</th></tr></thead>
          <tbody>
            {tickets.isLoading && <tr><td className="p-4" colSpan={6}>Loading tickets</td></tr>}
            {tickets.data?.items.map((ticket) => (
              <tr key={ticket.id} className="border-t border-line hover:bg-mist">
                <td className="p-3"><Link className="font-medium text-teal" to={`/tickets/${ticket.id}`}>{ticket.subject}</Link></td>
                <td><Badge tone={ticket.escalated ? "bad" : "neutral"}>{ticket.status}</Badge></td>
                <td><Badge tone={ticket.priority === "urgent" ? "bad" : ticket.priority === "high" ? "warn" : "neutral"}>{ticket.priority}</Badge></td>
                <td>{ticket.issue_category ?? "Pending"}</td>
                <td>{ticket.ai_confidence == null ? "-" : Math.round(ticket.ai_confidence * 100) + "%"}</td>
                <td>{ticket.customer_name}</td>
              </tr>
            ))}
            {tickets.data?.items.length === 0 && <tr><td className="p-4" colSpan={6}>No tickets match these filters.</td></tr>}
          </tbody>
        </table>
      </div>
    </section>
  );
}

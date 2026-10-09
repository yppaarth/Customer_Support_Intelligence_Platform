import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, RefreshCw, Send, X } from "lucide-react";
import { useState } from "react";
import { useParams } from "react-router-dom";
import { Badge } from "../components/Badge";
import { api } from "../lib/api";
import type { TicketDetail } from "../types/api";

export function TicketDetailPage() {
  const { ticketId } = useParams();
  const qc = useQueryClient();
  const ticket = useQuery({ queryKey: ["ticket", ticketId], queryFn: () => api<TicketDetail>(`/tickets/${ticketId}`), enabled: Boolean(ticketId) });
  const [draft, setDraft] = useState("");
  const action = useMutation({
    mutationFn: (body: Record<string, unknown>) => api(`/tickets/${ticketId}/actions`, { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["ticket", ticketId] })
  });
  const approve = useMutation({
    mutationFn: () => api(`/tickets/${ticketId}/approve`, { method: "POST", body: JSON.stringify({ draft_body: draft || ticket.data?.latest_draft?.body }) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["ticket", ticketId] })
  });
  const regenerate = useMutation({
    mutationFn: () => api(`/tickets/${ticketId}/regenerate`, { method: "POST" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["ticket", ticketId] })
  });

  if (ticket.isLoading) return <div>Loading ticket</div>;
  if (!ticket.data) return <div>Ticket not found</div>;
  const data = ticket.data;
  const body = draft || data.latest_draft?.body || "";
  return (
    <section className="grid gap-4 lg:grid-cols-[1fr_360px]">
      <div>
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold">{data.subject}</h1>
            <div className="mt-2 flex gap-2"><Badge>{data.status}</Badge><Badge tone={data.priority === "urgent" ? "bad" : "neutral"}>{data.priority}</Badge></div>
          </div>
          <div className="flex gap-2">
            <button className="focus-ring rounded border border-line bg-panel p-2" title="Regenerate draft" onClick={() => regenerate.mutate()}><RefreshCw size={18} /></button>
            <button className="focus-ring rounded border border-line bg-panel p-2" title="Reject draft" onClick={() => action.mutate({ status: "rejected" })}><X size={18} /></button>
            <button className="focus-ring rounded bg-teal p-2 text-white" title="Approve draft" onClick={() => approve.mutate()}><Check size={18} /></button>
          </div>
        </div>
        <div className="rounded border border-line bg-panel">
          {data.messages.map((m) => <div key={m.id} className="border-b border-line p-4"><div className="text-xs uppercase text-slate-500">{m.sender_type} {m.sender_name}</div><p className="mt-2 whitespace-pre-wrap">{m.body}</p></div>)}
        </div>
        <div className="mt-4 rounded border border-line bg-panel p-4">
          <div className="mb-2 flex items-center gap-2 font-semibold"><Send size={18} /> AI Draft</div>
          <textarea className="focus-ring min-h-52 w-full rounded border border-line p-3" value={body} onChange={(e) => setDraft(e.target.value)} />
          <div className="mt-3 flex gap-2">
            <button className="focus-ring rounded border border-line px-3 py-2 text-sm" onClick={() => action.mutate({ draft_body: body })}>Save edit</button>
            <button className="focus-ring rounded border border-line px-3 py-2 text-sm" onClick={() => action.mutate({ note: "Escalated by agent for manager review.", status: "escalated" })}>Escalate</button>
            <button className="focus-ring rounded border border-line px-3 py-2 text-sm" onClick={() => action.mutate({ status: "resolved" })}>Resolve</button>
          </div>
        </div>
      </div>
      <aside className="space-y-4">
        <div className="rounded border border-line bg-panel p-4">
          <h2 className="font-semibold">Customer</h2>
          <p className="mt-2 text-sm">{data.customer?.name} · {data.customer?.tier}</p>
          {data.order_context.map((o) => <p key={o.order_number} className="mt-2 text-sm">{o.order_number}: {o.status} (${o.total_amount})</p>)}
        </div>
        <div className="rounded border border-line bg-panel p-4">
          <h2 className="font-semibold">Classification</h2>
          <p className="mt-2 text-sm">{data.classification?.issue_category ?? "Pending"} · {data.classification?.sentiment}</p>
          <p className="mt-2 text-sm text-slate-600">{data.classification?.summary}</p>
          <div className="mt-2 flex flex-wrap gap-1">{data.classification?.risk_flags.map((f) => <Badge key={f} tone="bad">{f}</Badge>)}</div>
        </div>
        <div className="rounded border border-line bg-panel p-4">
          <h2 className="font-semibold">Sources</h2>
          <div className="mt-2 space-y-3">{data.latest_draft?.citations.map((c) => <div key={c.id} className="rounded border border-line p-3 text-sm"><div className="font-medium">{c.title}</div><p className="mt-1 text-slate-600">{c.quote}</p></div>)}</div>
        </div>
        {data.escalations.map((e) => <div key={e.id} className="rounded border border-rose/30 bg-rose/10 p-4 text-sm text-rose">{e.reason}</div>)}
      </aside>
    </section>
  );
}

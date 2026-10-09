import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";

export function KnowledgePage() {
  const q = useQuery({ queryKey: ["knowledge"], queryFn: () => api<Array<{ id: string; title: string; status: string; archived: boolean; chunk_count: number }>>("/knowledge") });
  return (
    <section>
      <h1 className="text-2xl font-semibold">Knowledge Base</h1>
      <div className="mt-4 grid gap-3 md:grid-cols-2">{q.data?.map((doc) => <div key={doc.id} className="rounded border border-line bg-panel p-4"><div className="font-semibold">{doc.title}</div><div className="mt-2 text-sm text-slate-500">{doc.status} · {doc.chunk_count} chunks</div></div>)}</div>
    </section>
  );
}

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Archive, Upload } from "lucide-react";
import { useState } from "react";
import { api, apiForm } from "../lib/api";

export function KnowledgePage() {
  const qc = useQueryClient();
  const [title, setTitle] = useState("Returns edge-case note");
  const [content, setContent] = useState("Refund exceptions must be reviewed when the item is used, the request is outside the 30 day window, or fraud indicators are present.");
  const [file, setFile] = useState<File | null>(null);
  const q = useQuery({ queryKey: ["knowledge"], queryFn: () => api<Array<{ id: string; title: string; status: string; archived: boolean; chunk_count: number }>>("/knowledge") });
  const create = useMutation({
    mutationFn: () => api("/knowledge", { method: "POST", body: JSON.stringify({ title, content, source_type: "markdown" }) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["knowledge"] })
  });
  const upload = useMutation({
    mutationFn: () => {
      if (!file) throw new Error("Choose a file first");
      const form = new FormData();
      form.append("title", title);
      form.append("file", file);
      return apiForm("/knowledge/upload", form);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["knowledge"] })
  });
  const archive = useMutation({
    mutationFn: (id: string) => api(`/knowledge/${id}/archive`, { method: "POST" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["knowledge"] })
  });
  return (
    <section>
      <h1 className="text-2xl font-semibold">Knowledge Base</h1>
      <div className="mt-4 rounded border border-line bg-panel p-4">
        <div className="grid gap-3 md:grid-cols-[220px_1fr_auto_auto]">
          <input className="focus-ring rounded border border-line px-3 py-2" value={title} onChange={(e) => setTitle(e.target.value)} />
          <input className="focus-ring rounded border border-line px-3 py-2" value={content} onChange={(e) => setContent(e.target.value)} />
          <button className="focus-ring rounded bg-teal px-3 py-2 text-sm font-medium text-white" onClick={() => create.mutate()}>Add text</button>
          <label className="focus-ring inline-flex cursor-pointer items-center gap-2 rounded border border-line px-3 py-2 text-sm">
            <Upload size={16} /> File
            <input className="hidden" type="file" accept=".txt,.md,.markdown,.html,.htm" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
          </label>
        </div>
        {file && <button className="focus-ring mt-3 rounded border border-line px-3 py-2 text-sm" onClick={() => upload.mutate()}>Upload {file.name}</button>}
        {(create.error || upload.error) && <p className="mt-3 text-sm text-rose">{(create.error || upload.error)?.message}</p>}
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-2">{q.data?.map((doc) => <div key={doc.id} className="rounded border border-line bg-panel p-4"><div className="flex items-center justify-between gap-3"><div className="font-semibold">{doc.title}</div><button className="focus-ring rounded border border-line p-2" title="Archive document" onClick={() => archive.mutate(doc.id)}><Archive size={16} /></button></div><div className="mt-2 text-sm text-slate-500">{doc.status} · {doc.chunk_count} chunks</div></div>)}</div>
    </section>
  );
}

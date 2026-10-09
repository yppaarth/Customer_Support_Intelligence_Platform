import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { api } from "../lib/api";

export function SettingsPage() {
  const qc = useQueryClient();
  const q = useQuery({ queryKey: ["settings"], queryFn: () => api<{ autonomous_send_enabled: boolean; retention_days: number; model_settings: Record<string, unknown> }>("/settings") });
  const [retention, setRetention] = useState(365);
  const [autonomous, setAutonomous] = useState(false);
  useEffect(() => {
    if (q.data) {
      setRetention(q.data.retention_days);
      setAutonomous(q.data.autonomous_send_enabled);
    }
  }, [q.data]);
  const save = useMutation({
    mutationFn: () => api("/settings", { method: "PATCH", body: JSON.stringify({ retention_days: retention, autonomous_send_enabled: autonomous }) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["settings"] })
  });
  return (
    <section>
      <h1 className="text-2xl font-semibold">Model And Escalation Settings</h1>
      <div className="mt-4 max-w-xl rounded border border-line bg-panel p-4">
        <label className="flex items-center justify-between gap-4 text-sm"><span>Autonomous customer sends</span><input type="checkbox" checked={autonomous} onChange={(e) => setAutonomous(e.target.checked)} /></label>
        <label className="mt-4 block text-sm">Retention days</label>
        <input className="focus-ring mt-1 w-full rounded border border-line px-3 py-2" type="number" min={1} max={3650} value={retention} onChange={(e) => setRetention(Number(e.target.value))} />
        <button className="focus-ring mt-4 rounded bg-teal px-3 py-2 text-sm font-medium text-white" onClick={() => save.mutate()}>Save settings</button>
        {save.error && <p className="mt-3 text-sm text-rose">{save.error.message}</p>}
      </div>
    </section>
  );
}

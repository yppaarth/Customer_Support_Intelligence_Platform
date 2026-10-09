import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, setToken } from "../lib/api";

export function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("admin@northstar.demo");
  const [password, setPassword] = useState("ResolveIQDemo!23");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await api<{ access_token: string }>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password, organization_slug: "northstar" })
      });
      setToken(response.access_token);
      navigate("/tickets");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="grid min-h-screen place-items-center bg-mist p-4">
      <form onSubmit={submit} className="w-full max-w-sm rounded border border-line bg-panel p-6 shadow-sm">
        <h1 className="text-2xl font-semibold">ResolveIQ</h1>
        <p className="mt-1 text-sm text-slate-500">Northstar Commerce support workspace</p>
        <label className="mt-6 block text-sm font-medium">Email</label>
        <input className="focus-ring mt-1 w-full rounded border border-line px-3 py-2" value={email} onChange={(e) => setEmail(e.target.value)} />
        <label className="mt-4 block text-sm font-medium">Password</label>
        <input className="focus-ring mt-1 w-full rounded border border-line px-3 py-2" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        {error && <div className="mt-4 rounded border border-rose/30 bg-rose/10 p-3 text-sm text-rose">{error}</div>}
        <button className="focus-ring mt-6 w-full rounded bg-teal px-4 py-2 font-medium text-white disabled:opacity-60" disabled={loading}>
          {loading ? "Signing in" : "Sign in"}
        </button>
      </form>
    </main>
  );
}

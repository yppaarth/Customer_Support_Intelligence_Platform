const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000/api/v1";

export function getToken(): string | null {
  return localStorage.getItem("resolveiq_token");
}

export function setToken(token: string): void {
  localStorage.setItem("resolveiq_token", token);
}

export function clearToken(): void {
  localStorage.removeItem("resolveiq_token");
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken();
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "content-type": "application/json",
      ...(token ? { authorization: `Bearer ${token}` } : {}),
      ...init.headers
    }
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail ?? "Request failed");
  }
  return res.json() as Promise<T>;
}

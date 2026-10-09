import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";

export function UsersPage() {
  const q = useQuery({ queryKey: ["users"], queryFn: () => api<Array<{ id: string; email: string; full_name: string; role: string }>>("/users") });
  return <section><h1 className="text-2xl font-semibold">Users And Roles</h1><div className="mt-4 overflow-hidden rounded border border-line bg-panel"><table className="w-full text-left text-sm"><tbody>{q.data?.map((u) => <tr key={u.id} className="border-t border-line"><td className="p-3 font-medium">{u.full_name}</td><td>{u.email}</td><td>{u.role}</td></tr>)}</tbody></table></div></section>;
}

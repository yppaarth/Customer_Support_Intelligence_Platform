import { Link } from "react-router-dom";

export function AccessDeniedPage() {
  return <main className="grid min-h-[60vh] place-items-center"><div><h1 className="text-2xl font-semibold">Access denied</h1><p className="mt-2 text-sm text-slate-500">Your role does not allow that action.</p><Link className="mt-3 block text-teal" to="/tickets">Return to inbox</Link></div></main>;
}

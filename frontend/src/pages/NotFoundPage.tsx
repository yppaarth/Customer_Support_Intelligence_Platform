import { Link } from "react-router-dom";

export function NotFoundPage() {
  return <main className="grid min-h-screen place-items-center"><div><h1 className="text-2xl font-semibold">Page not found</h1><Link className="mt-3 block text-teal" to="/tickets">Return to inbox</Link></div></main>;
}

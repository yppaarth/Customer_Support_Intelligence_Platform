import { BarChart3, BookOpen, ClipboardList, LogOut, ShieldAlert, Users, Wrench } from "lucide-react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { clearToken } from "../lib/api";

const links = [
  { to: "/tickets", label: "Inbox", icon: ClipboardList },
  { to: "/knowledge", label: "Knowledge", icon: BookOpen },
  { to: "/escalations", label: "Escalations", icon: ShieldAlert },
  { to: "/analytics", label: "Analytics", icon: BarChart3 },
  { to: "/evaluations", label: "Evaluations", icon: Wrench },
  { to: "/users", label: "Users", icon: Users }
];

export function Layout() {
  const navigate = useNavigate();
  return (
    <div className="min-h-screen">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-line bg-panel p-4 md:block">
        <div className="mb-6">
          <div className="text-xl font-semibold">ResolveIQ</div>
          <div className="text-sm text-slate-500">Northstar Commerce</div>
        </div>
        <nav className="space-y-1">
          {links.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} className={({ isActive }) => `flex items-center gap-3 rounded px-3 py-2 text-sm ${isActive ? "bg-teal text-white" : "hover:bg-mist"}`}>
              <Icon size={18} /> {label}
            </NavLink>
          ))}
        </nav>
        <button className="focus-ring absolute bottom-4 flex items-center gap-2 rounded px-3 py-2 text-sm hover:bg-mist" onClick={() => { clearToken(); navigate("/login"); }}>
          <LogOut size={18} /> Sign out
        </button>
      </aside>
      <main className="md:pl-64">
        <div className="mx-auto max-w-7xl p-4 md:p-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}

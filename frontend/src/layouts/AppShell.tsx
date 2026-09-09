import { ReactNode } from "react";
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export default function AppShell({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const location = useLocation();

  const navItems =
    user?.role === "manager"
      ? [
          { to: "/manager", label: "Dashboard" },
          { to: "/manager/ai-command-center", label: "AI Command Center" },
          { to: "/manager/maintenance", label: "Maintenance" },
          { to: "/manager/inventory", label: "Inventory" },
          { to: "/manager/staff", label: "Staff" },
          { to: "/manager/revenue", label: "Revenue" },
          { to: "/manager/guests", label: "Guests" },
        ]
      : [];

  return (
    <div className="min-h-screen">
      <header className="border-b border-white/5 bg-charcoal-900/60 backdrop-blur sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <div>
              <p className="font-display text-lg leading-none">ResortIQ</p>
              <p className="text-[11px] text-slate-500 leading-none mt-0.5">Azure Valley Resort</p>
            </div>
            <nav className="hidden sm:flex gap-1">
              {navItems.map((item) => (
                <Link
                  key={item.to}
                  to={item.to}
                  className={`px-3 py-1.5 rounded-md text-sm transition ${
                    location.pathname === item.to
                      ? "bg-amber-500/15 text-amber-400"
                      : "text-slate-400 hover:text-slate-200 hover:bg-white/5"
                  }`}
                >
                  {item.label}
                </Link>
              ))}
            </nav>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right hidden sm:block">
              <p className="text-sm">{user?.name}</p>
              <p className="text-[11px] text-slate-500 capitalize">{user?.role}</p>
            </div>
            <button
              onClick={logout}
              className="text-xs px-3 py-1.5 rounded-md border border-white/10 text-slate-400 hover:text-slate-200 hover:border-white/20 transition"
            >
              Sign out
            </button>
          </div>
        </div>
      </header>
      <main className="max-w-7xl mx-auto px-6 py-8">{children}</main>
    </div>
  );
}

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";

const NAV_ITEMS = [{ href: "/", label: "Dashboard", icon: "▦" }];

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <aside className="flex w-64 shrink-0 flex-col border-r border-slate-200 bg-white">
      {/* Logo */}
      <div className="flex items-center gap-2 px-6 py-5">
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-sm font-bold text-white">
          D
        </span>
        <span className="text-lg font-semibold text-slate-900">DocuMind</span>
      </div>

      {/* Main navigation */}
      <nav className="space-y-1 px-3">
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium ${
                active ? "bg-indigo-50 text-indigo-700" : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              <span aria-hidden>{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Documents list (filled in by the next milestone) */}
      <div className="mt-6 flex-1 overflow-y-auto px-3">
        <p className="px-3 text-xs font-semibold uppercase tracking-wide text-slate-400">
          Documents
        </p>
        <p className="px-3 py-2 text-sm text-slate-400">No documents yet</p>
      </div>

      {/* Current user + log out */}
      <div className="border-t border-slate-200 p-4">
        <p className="truncate text-sm text-slate-700" title={user.email}>
          {user.email}
        </p>
        <button
          type="button"
          onClick={logout}
          className="mt-2 text-sm font-medium text-slate-500 hover:text-red-600"
        >
          Log out
        </button>
      </div>
    </aside>
  );
}

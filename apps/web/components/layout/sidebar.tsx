"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  ClipboardList,
  HeartHandshake,
  HeartPulse,
  LayoutDashboard,
  LogOut,
  Settings,
  Users,
} from "lucide-react";
import { useAuth } from "@/components/providers/auth-provider";
import { ROLE_LABELS } from "@/lib/constants";
import { initials } from "@/lib/format";
import { cn } from "@/lib/cn";

const ALL_NAV = [
  { href: "/care", label: "Care", icon: HeartHandshake, permission: "caregiver_report.read" },
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard, permission: null },
  { href: "/patients", label: "Patients", icon: Users, permission: "patient.read" },
  { href: "/visits", label: "Visits", icon: ClipboardList, permission: "visit.read" },
  { href: "/tasks", label: "Tasks", icon: HeartPulse, permission: "care_task.read" },
  { href: "/settings", label: "Settings", icon: Settings, permission: null },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout, canAccess } = useAuth();

  const nav = ALL_NAV.filter(
    (item) => item.permission === null || canAccess(item.permission),
  ).filter((item) => {
    // The Care workspace is for caregivers and the team; keep employees on
    // their normal workspace pages once they have their own.
    if (item.href === "/care") return user?.role === "CAREGIVER";
    return true;
  });

  return (
    <aside className="hidden w-60 shrink-0 flex-col border-r border-line bg-surface md:flex">
      <Link href="/dashboard" className="flex items-center gap-2.5 px-5 py-5">
        <span className="flex h-8 w-8 items-center justify-center rounded-md bg-brand-700 text-white">
          <HeartPulse className="h-4 w-4" aria-hidden />
        </span>
        <span className="text-[15px] font-semibold tracking-tight text-slate-900">
          Pallia OS
        </span>
      </Link>

      <nav className="mt-2 flex-1 space-y-0.5 px-3">
        {nav.map((item) => {
          const active =
            item.href === "/dashboard"
              ? pathname === "/dashboard"
              : pathname.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              aria-current={active ? "page" : undefined}
              className={cn(
                "flex items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                active
                  ? "bg-brand-50 text-brand-800"
                  : "text-slate-600 hover:bg-slate-50 hover:text-slate-900",
              )}
            >
              <Icon className="h-4 w-4" aria-hidden />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-line px-5 py-4">
        <div className="flex items-center gap-3">
          <span className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-100 text-sm font-semibold text-slate-700">
            {initials(user?.full_name)}
          </span>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-slate-800">{user?.full_name}</p>
            <p className="truncate text-xs text-muted">
              {user ? ROLE_LABELS[user.role] ?? user.role : "—"}
            </p>
          </div>
          <button
            onClick={() => void logout()}
            className="rounded-md p-1.5 text-muted hover:bg-slate-100 hover:text-slate-700"
            title="Sign out"
            aria-label="Sign out"
          >
            <LogOut className="h-4 w-4" aria-hidden />
          </button>
        </div>
      </div>
    </aside>
  );
}
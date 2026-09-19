"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
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
import { cn } from "@/lib/cn";

const ALL_NAV = [
  { href: "/care", label: "Care", icon: HeartHandshake, permission: "caregiver_report.read" },
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard, permission: null },
  { href: "/patients", label: "Patients", icon: Users, permission: "patient.read" },
  { href: "/visits", label: "Visits", icon: ClipboardList, permission: "visit.read" },
  { href: "/tasks", label: "Tasks", icon: HeartPulse, permission: "care_task.read" },
  { href: "/settings", label: "Settings", icon: Settings, permission: null },
];

/** Compact top bar shown on small screens, replacing the sidebar. */
export function MobileNav() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout, canAccess } = useAuth();

  const nav = ALL_NAV.filter(
    (item) => item.permission === null || canAccess(item.permission),
  ).filter((item) => {
    if (item.href === "/care") return user?.role === "CAREGIVER";
    return true;
  });

  return (
    <header className="flex items-center justify-between border-b border-line bg-surface px-4 py-3 md:hidden">
      <Link href="/dashboard" className="flex items-center gap-2">
        <span className="flex h-7 w-7 items-center justify-center rounded-md bg-brand-700 text-white">
          <HeartPulse className="h-3.5 w-3.5" aria-hidden />
        </span>
        <span className="text-sm font-semibold text-slate-900">Pallia OS</span>
      </Link>
      <nav className="flex items-center gap-1">
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
              aria-label={item.label}
              title={item.label}
              className={cn(
                "rounded-md p-2",
                active ? "bg-brand-50 text-brand-800" : "text-slate-500 hover:bg-slate-100",
              )}
            >
              <Icon className="h-4 w-4" aria-hidden />
            </Link>
          );
        })}
        <button
          onClick={() => {
            void logout();
            router.push("/login");
          }}
          aria-label="Sign out"
          className="rounded-md p-2 text-slate-500 hover:bg-slate-100"
        >
          <LogOut className="h-4 w-4" aria-hidden />
        </button>
      </nav>
    </header>
  );
}
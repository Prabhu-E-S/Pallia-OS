"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { AuthProvider, useAuth } from "@/components/providers/auth-provider";
import { Sidebar } from "@/components/layout/sidebar";
import { MobileNav } from "@/components/layout/mobile-nav";
import { PageLoader } from "@/components/ui/feedback";

function GuardedShell({ children }: { children: React.ReactNode }) {
  const { user, ready } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!ready) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    // Caregivers land in the Care workspace, not the employee dashboard.
    if (user.role === "CAREGIVER" && pathname === "/dashboard") {
      router.replace("/care");
    }
  }, [ready, user, router, pathname]);

  if (!ready) return <PageLoader label="Preparing workspace…" />;
  if (!user) return null;

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <MobileNav />
        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 md:px-8">
          {children}
        </main>
      </div>
    </div>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <GuardedShell>{children}</GuardedShell>
    </AuthProvider>
  );
}
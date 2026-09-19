"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { PageLoader } from "@/components/ui/feedback";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    // The AppShell guard resolves the session (incl. silent refresh) and
    // redirects unauthenticated visitors to /login.
    router.replace("/dashboard");
  }, [router]);

  return <PageLoader label="Opening Pallia OS…" />;
}
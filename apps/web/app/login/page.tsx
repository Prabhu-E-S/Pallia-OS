"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { HeartPulse } from "lucide-react";
import { ApiErrorResponse } from "@/lib/api/client";
import { AuthProvider, useAuth } from "@/components/providers/auth-provider";
import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/field";

const DEMO_HINT = [
  "admin@pallia.demo",
  "coordinator@pallia.demo",
  "nurse@pallia.demo",
  "doctor@pallia.demo",
  "caregiver@pallia.demo",
  "patient@pallia.demo",
];

function LoginForm() {
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState("admin@pallia.demo");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (submitting || !email.trim() || !password) return;
    setSubmitting(true);
    setError(null);
    try {
      await login(email.trim(), password);
      router.replace("/dashboard");
    } catch (err) {
      const message =
        err instanceof ApiErrorResponse ? err.message : "Unable to sign in. Is the API running?";
      setError(message);
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="mb-8 flex flex-col items-center text-center">
          <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand-700 text-white shadow-card">
            <HeartPulse className="h-6 w-6" aria-hidden />
          </span>
          <h1 className="mt-4 text-2xl font-semibold tracking-tight text-slate-900">
            Pallia OS
          </h1>
          <p className="mt-1 text-sm text-muted">Sign in to your care workspace</p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="rounded-xl border border-line bg-surface p-6 shadow-card"
        >
          <Field label="Email" htmlFor="email">
            <Input
              id="email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              autoComplete="email"
              required
            />
          </Field>

          <div className="mt-4">
            <Field label="Password" htmlFor="password">
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                autoComplete="current-password"
                placeholder="••••••••••"
                required
              />
            </Field>
          </div>

          {error ? (
            <p role="alert" className="mt-4 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-800">
              {error}
            </p>
          ) : null}

          <Button type="submit" disabled={submitting} className="mt-5 w-full">
            {submitting ? "Signing in…" : "Sign in"}
          </Button>
        </form>

        <p className="mt-6 text-center text-xs text-muted">
          Demo password: <span className="font-medium text-slate-600">pallia123</span>
        </p>
        <p className="mt-1.5 text-center text-xs">
          {DEMO_HINT.join(" · ")}
        </p>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <AuthProvider>
      <LoginForm />
    </AuthProvider>
  );
}
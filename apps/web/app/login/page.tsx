"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { HeartPulse } from "lucide-react";
import { authApi } from "@/lib/api/auth";
import { ApiErrorResponse } from "@/lib/api/client";
import { AuthProvider, useAuth } from "@/components/providers/auth-provider";
import { Button } from "@/components/ui/button";
import { Field, Input, Select } from "@/components/ui/field";

const DEMO_ACCOUNTS = [
  { email: "admin@pallia.demo", label: "Administrator" },
  { email: "coordinator@pallia.demo", label: "Care coordinator" },
  { email: "nurse@pallia.demo", label: "Nurse (Savitri Rao)" },
  { email: "nurse2@pallia.demo", label: "Nurse (Meera Nair)" },
  { email: "doctor@pallia.demo", label: "Doctor" },
  { email: "caregiver@pallia.demo", label: "Caregiver" },
];

function LoginForm() {
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState(DEMO_ACCOUNTS[1].email);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      const response = await authApi().devLogin(email.trim());
      login({ token: response.access_token, user: response.user });
      router.push("/dashboard");
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
          <p className="mt-1 text-sm text-muted">
            Sign in to your care workspace
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="rounded-xl border border-line bg-surface p-6 shadow-card"
        >
          <Field label="Demo account" htmlFor="demo-account">
            <Select
              id="demo-account"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            >
              {DEMO_ACCOUNTS.map((account) => (
                <option key={account.email} value={account.email}>
                  {account.label}
                </option>
              ))}
            </Select>
          </Field>

          <div className="mt-4">
            <Field label="Email" htmlFor="email">
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                autoComplete="email"
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
          Development login — replaces production authentication in Phase 1.
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
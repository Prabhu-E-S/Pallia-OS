"use client";

import { useAuth } from "@/components/providers/auth-provider";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { PageHeader } from "@/components/ui/page";
import { Badge } from "@/components/ui/badge";
import { ROLE_LABELS, STATUS_LABELS } from "@/lib/constants";
import { initials } from "@/lib/format";

const DEMO_ACCOUNTS = [
  { email: "admin@pallia.demo", role: "Administrator (org A)" },
  { email: "coordinator@pallia.demo", role: "Care coordinator (org A)" },
  { email: "nurse@pallia.demo", role: "Nurse (org A)" },
  { email: "nurse2@pallia.demo", role: "Nurse (org A)" },
  { email: "doctor@pallia.demo", role: "Doctor (org A)" },
  { email: "caregiver@pallia.demo", role: "Caregiver — linked patients only (org A)" },
  { email: "patient@pallia.demo", role: "Patient — own record only (org A)" },
  { email: "admin@willowcreek.demo", role: "Administrator (org B)" },
  { email: "nurse@willowcreek.demo", role: "Nurse (org B)" },
  { email: "caregiver@willowcreek.demo", role: "Caregiver (org B)" },
  { email: "patient@willowcreek.demo", role: "Patient (org B)" },
];

export default function SettingsPage() {
  const { user } = useAuth();

  return (
    <div className="space-y-6">
      <PageHeader title="Settings" description="Workspace and account details" />

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader title="Your account" description="Signed-in profile" />
          <CardBody>
            <div className="flex items-center gap-4">
              <span className="flex h-12 w-12 items-center justify-center rounded-full bg-brand-50 text-lg font-semibold text-brand-800">
                {initials(user?.full_name)}
              </span>
              <div>
                <p className="text-sm font-semibold text-slate-900">{user?.full_name}</p>
                <p className="text-xs text-muted">{user?.email}</p>
                <p className="mt-0.5 text-xs text-muted">{user?.organization_name}</p>
              </div>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              <Badge tone="teal">{user ? ROLE_LABELS[user.role] ?? user.role : "—"}</Badge>
              <Badge tone="neutral">{user ? STATUS_LABELS[user.status] ?? user.status : "—"}</Badge>
              <Badge tone="neutral">{user?.permissions.length ?? 0} permissions</Badge>
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="Demo accounts" description="Development sign-in users (password: pallia123)" />
          <CardBody>
            <ul className="divide-y divide-line">
              {DEMO_ACCOUNTS.map((account) => (
                <li key={account.email} className="flex items-center justify-between py-2.5">
                  <div>
                    <p className="text-sm font-medium text-slate-800">{account.role}</p>
                    <p className="text-xs text-muted">{account.email}</p>
                  </div>
                  <Badge tone="neutral">{account.email.split("@")[0]}</Badge>
                </li>
              ))}
            </ul>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
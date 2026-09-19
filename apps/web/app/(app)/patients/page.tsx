"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Search, UserPlus } from "lucide-react";
import { patientsApi } from "@/lib/api/patients";
import { ApiErrorResponse } from "@/lib/api/client";
import type { PatientSummary } from "@/lib/api/types";
import { useAuth } from "@/components/providers/auth-provider";
import { PageHeader } from "@/components/ui/page";
import { Table } from "@/components/ui/table";
import { StatusBadge } from "@/components/status-badge";
import { EmptyState, PageLoader } from "@/components/ui/feedback";
import { Button } from "@/components/ui/button";
import { Field, Input, Select } from "@/components/ui/field";
import { ageFrom, formatDate, initials } from "@/lib/format";
import { cn } from "@/lib/cn";

const STATUS_FILTERS = [
  { value: "", label: "All statuses" },
  { value: "ACTIVE", label: "Active" },
  { value: "INACTIVE", label: "Inactive" },
  { value: "DISCHARGED", label: "Discharged" },
  { value: "DECEASED", label: "Deceased" },
  { value: "TRANSFERRED", label: "Transferred" },
];

export default function PatientsPage() {
  const router = useRouter();
  const { canAccess } = useAuth();
  const [items, setItems] = useState<PatientSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");

  useEffect(() => {
    let cancelled = false;
    patientsApi()
      .list({ q: query || undefined, status: status || undefined })
      .then((result) => {
        if (cancelled) return;
        setItems(result.items);
        setError(null);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err instanceof ApiErrorResponse ? err.message : "Unable to load patients.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [query, status]);

  const rows = items.map((patient) => ({
    key: patient.id,
    name: <PatientCell patient={patient} />,
    dob: formatDate(patient.date_of_birth),
    age: ageFrom(patient.date_of_birth) ?? "—",
    language: patient.preferred_language ?? "—",
    phone: patient.phone ?? "—",
    status: <StatusBadge value={patient.status} />,
  }));

  return (
    <div className="space-y-6">
      <PageHeader
        title="Patients"
        description={`${items.length} people under care`}
        actions={
          canAccess("patient.create") ? (
            <Button
              onClick={() => router.push("/dashboard")}
              variant="secondary"
            >
              <UserPlus className="h-4 w-4" aria-hidden />
              New patient
            </Button>
          ) : undefined
        }
      />

      <div className="flex flex-wrap items-end gap-3">
        <div className="w-full max-w-xs">
          <Field label="Search">
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden />
              <Input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search by name…"
                className="pl-9"
                aria-label="Search patients"
              />
            </div>
          </Field>
        </div>
        <div className="w-44">
          <Field label="Status">
            <Select value={status} onChange={(event) => setStatus(event.target.value)} aria-label="Filter by status">
              {STATUS_FILTERS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </Select>
          </Field>
        </div>
      </div>

      <div className="mt-4">
        {loading ? (
          <PageLoader label="Loading patients…" />
        ) : error ? (
          <EmptyState title="Something went wrong" description={error} />
        ) : (
          <Table
            columns={[
              { key: "name", header: "Patient" },
              { key: "dob", header: "Date of birth" },
              { key: "age", header: "Age" },
              { key: "language", header: "Language" },
              { key: "phone", header: "Phone" },
              { key: "status", header: "Status" },
            ]}
            rows={rows}
            rowKey={(row) => String(row.key)}
            empty={<EmptyState title="No matching patients" description="Try changing the filters." />}
            onRowClick={(row) => router.push(`/patients/${String(row.key)}`)}
          />
        )}
      </div>
    </div>
  );
}

function PatientCell({ patient }: { patient: PatientSummary }) {
  return (
    <div className="flex items-center gap-3">
      <span
        className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-semibold",
          patient.status === "ACTIVE"
            ? "bg-brand-50 text-brand-800"
            : "bg-slate-100 text-slate-500",
        )}
      >
        {initials(patient.full_name)}
      </span>
      <span className="font-medium text-slate-900">{patient.full_name}</span>
    </div>
  );
}
"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Plus } from "lucide-react";
import { visitsApi } from "@/lib/api/records";
import { patientsApi } from "@/lib/api/patients";
import { ApiErrorResponse } from "@/lib/api/client";
import type { PatientSummary, Visit } from "@/lib/api/types";
import { useAuth } from "@/components/providers/auth-provider";
import { PageHeader } from "@/components/ui/page";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { Table } from "@/components/ui/table";
import { StatusBadge } from "@/components/status-badge";
import { EmptyState, PageLoader } from "@/components/ui/feedback";
import { Button } from "@/components/ui/button";
import { Field, Input, Select, Textarea } from "@/components/ui/field";
import { formatDateTime, toIsoLocal } from "@/lib/format";

const FILTERS = [
  { value: "", label: "All statuses" },
  { value: "SCHEDULED", label: "Scheduled" },
  { value: "IN_PROGRESS", label: "In progress" },
  { value: "COMPLETED", label: "Completed" },
  { value: "CANCELLED", label: "Cancelled" },
];

export default function VisitsPage() {
  const router = useRouter();
  const { canAccess } = useAuth();
  const [items, setItems] = useState<Visit[]>([]);
  const [patients, setPatients] = useState<PatientSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      visitsApi().list({ status: status || undefined }),
      patientsApi().list({ status: "ACTIVE" }),
    ])
      .then(([visits, people]) => {
        if (cancelled) return;
        setItems(visits.items);
        setPatients(people.items);
        setError(null);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err instanceof ApiErrorResponse ? err.message : "Unable to load visits.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [status, reloadToken]);

  const rows = items.map((visit) => ({
    key: visit.id,
    patient: (
      <button
        onClick={() => router.push(`/patients/${visit.patient_id}`)}
        className="text-sm font-medium text-brand-800 hover:underline"
      >
        {visit.patient_name ?? "Patient"}
      </button>
    ),
    when: formatDateTime(visit.scheduled_at),
    assigned: visit.assigned_to_name ?? "Unassigned",
    notes: visit.notes ?? "—",
    status: <StatusBadge value={visit.status} />,
  }));

  return (
    <div className="space-y-6">
      <PageHeader
        title="Visits"
        description="Home visits across the team"
        actions={
          canAccess("visit.create") ? (
            <Button onClick={() => setShowForm((value) => !value)}>
              <Plus className="h-4 w-4" aria-hidden />
              Schedule visit
            </Button>
          ) : undefined
        }
      />

      {showForm ? (
        <VisitForm patients={patients} onCreated={() => { setShowForm(false); setReloadToken((value) => value + 1); }} />
      ) : null}

      <div className="flex w-56">
        <Field label="Status">
          <Select value={status} onChange={(event) => setStatus(event.target.value)} aria-label="Filter visits">
            {FILTERS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>
        </Field>
      </div>

      <div>
        {loading ? (
          <PageLoader label="Loading visits…" />
        ) : error ? (
          <EmptyState title="Something went wrong" description={error} />
        ) : (
          <Table
            columns={[
              { key: "patient", header: "Patient" },
              { key: "when", header: "Scheduled" },
              { key: "assigned", header: "Assigned to" },
              { key: "notes", header: "Notes" },
              { key: "status", header: "Status" },
            ]}
            rows={rows}
            rowKey={(row) => String(row.key)}
            empty={<EmptyState title="No visits" description="Schedule a visit to get started." />}
          />
        )}
      </div>
    </div>
  );
}

function VisitForm({
  patients,
  onCreated,
}: {
  patients: PatientSummary[];
  onCreated: () => void;
}) {
  const [patientId, setPatientId] = useState(patients[0]?.id ?? "");
  const [scheduledAt, setScheduledAt] = useState(toIsoLocal(new Date()));
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!patientId || !scheduledAt) return;
    setSaving(true);
    setError(null);
    try {
      await visitsApi().create({
        patient_id: patientId,
        scheduled_at: new Date(scheduledAt).toISOString(),
        notes: notes.trim() || null,
      });
      onCreated();
    } catch (err) {
      setError(err instanceof ApiErrorResponse ? err.message : "Unable to schedule visit.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card>
      <CardHeader title="Schedule a visit" description="Plan a home visit for a patient" />
      <CardBody>
        <form onSubmit={submit} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Field label="Patient" htmlFor="visit-patient">
            <Select id="visit-patient" value={patientId} onChange={(event) => setPatientId(event.target.value)} required>
              {patients.map((patient) => (
                <option key={patient.id} value={patient.id}>
                  {patient.full_name}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Scheduled time" htmlFor="visit-when" hint="Local time">
            <Input
              id="visit-when"
              type="datetime-local"
              value={scheduledAt}
              onChange={(event) => setScheduledAt(event.target.value)}
              required
            />
          </Field>
          <Field label="Notes" htmlFor="visit-notes" className="sm:col-span-2 lg:col-span-1">
            <Textarea
              id="visit-notes"
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              placeholder="Purpose of the visit…"
              className="h-10 min-h-10"
            />
          </Field>
          {error ? (
            <p className="text-sm text-rose-700" role="alert">
              {error}
            </p>
          ) : null}
          <div className="flex items-center gap-2 sm:col-span-2 lg:col-span-3">
            <Button type="submit" disabled={saving || patients.length === 0}>
              {saving ? "Scheduling…" : "Schedule visit"}
            </Button>
            {patients.length === 0 ? (
              <span className="text-xs text-muted">No active patients available.</span>
            ) : null}
          </div>
        </form>
      </CardBody>
    </Card>
  );
}
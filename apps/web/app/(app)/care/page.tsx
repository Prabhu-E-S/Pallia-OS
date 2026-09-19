"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Eye, Plus } from "lucide-react";
import { patientsApi } from "@/lib/api/patients";
import { reportsApi } from "@/lib/api/reports";
import { ApiErrorResponse } from "@/lib/api/client";
import type { CaregiverReport, PatientSummary } from "@/lib/api/types";
import { PageHeader } from "@/components/ui/page";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { StatusBadge } from "@/components/status-badge";
import { EmptyState, PageLoader } from "@/components/ui/feedback";
import { ReportWizard } from "@/components/care/report-wizard";
import { REPORT_MODE_LABELS, REPORT_STATUS_LABELS } from "@/lib/constants";
import { ageFrom, formatDateTime, initials } from "@/lib/format";

interface WizardState {
  patient: PatientSummary;
  report?: CaregiverReport;
  mode?: "QUICK_STATUS" | "STRUCTURED" | "TEXT" | "VOICE";
}

export default function CarePage() {
  const router = useRouter();
  const [patients, setPatients] = useState<PatientSummary[]>([]);
  const [reportsByPatient, setReportsByPatient] = useState<
    Record<string, CaregiverReport[]>
  >({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);
  const [wizard, setWizard] = useState<WizardState | null>(null);

  useEffect(() => {
    let cancelled = false;
    patientsApi()
      .list()
      .then(async (result) => {
        if (cancelled) return;
        const patients = result.items;
        setPatients(patients);
        if (patients.length === 0) {
          setReportsByPatient({});
          setError(null);
          return;
        }
        const entries = await Promise.all(
          patients.map(async (patient) => [patient.id, (await reportsApi().list(patient.id)).items] as const),
        );
        if (cancelled) return;
        setReportsByPatient(Object.fromEntries(entries));
        setError(null);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err instanceof ApiErrorResponse ? err.message : "Unable to load your care updates.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [reloadToken]);

  const attention: Array<{ patient: PatientSummary; report: CaregiverReport }> = [];
  for (const patient of patients) {
    for (const report of reportsByPatient[patient.id] ?? []) {
      if (report.status === "REVIEW_REQUIRED") attention.push({ patient, report });
    }
  }

  if (loading) return <PageLoader label="Loading care updates…" />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Care"
        description="Report today's status and keep the care team up to date."
      />

      {error ? (
        <Card>
          <CardBody>
            <EmptyState
              title="Could not load updates"
              description={error}
              action={
                <Button variant="secondary" onClick={() => setReloadToken((value) => value + 1)}>
                  Try again
                </Button>
              }
            />
          </CardBody>
        </Card>
      ) : patients.length === 0 ? (
        <Card>
          <CardBody>
            <EmptyState
              title="No patients assigned"
              description="You don't have any patients linked to your account yet. Ask your care coordinator to link you."
            />
          </CardBody>
        </Card>
      ) : (
        <>
          {attention.length > 0 ? (
            <Card>
              <CardHeader
                title="Needs your attention"
                description="Voice updates drafted by the assistant and waiting for your confirmation."
              />
              <CardBody className="pt-0">
                <ul className="divide-y divide-line">
                  {attention.map(({ patient, report }) => (
                    <li key={report.id} className="flex items-center justify-between gap-4 py-3">
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-slate-800">
                          {patient.full_name}
                          <span className="ml-2 text-xs font-normal text-muted">
                            {formatDateTime(report.reported_at)}
                          </span>
                        </p>
                        <p className="mt-0.5 truncate text-xs text-muted">
                          {report.transcript ?? "Voice update"}
                        </p>
                      </div>
                      <Button size="sm" onClick={() => setWizard({ patient, report })}>
                        <Eye className="h-4 w-4" aria-hidden />
                        Review
                      </Button>
                    </li>
                  ))}
                </ul>
              </CardBody>
            </Card>
          ) : null}

          <div className="grid gap-4 md:grid-cols-2">
            {patients.map((patient) => {
              const reports = reportsByPatient[patient.id] ?? [];
              const openReport = attention.find((item) => item.patient.id === patient.id)?.report;
              return (
                <Card key={patient.id}>
                  <CardBody className="space-y-4">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex min-w-0 items-center gap-3">
                        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-brand-50 text-sm font-semibold text-brand-700">
                          {initials(patient.full_name)}
                        </span>
                        <div className="min-w-0">
                          <p className="truncate text-sm font-semibold text-slate-900">
                            {patient.full_name}
                          </p>
                          <p className="text-xs text-muted">
                            {ageFrom(patient.date_of_birth) ?? "—"} years
                            {patient.preferred_language ? ` · ${patient.preferred_language}` : ""}
                          </p>
                        </div>
                      </div>
                      <StatusBadge value={patient.status} />
                    </div>

                    {openReport ? (
                      <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2">
                        <p className="text-xs font-medium text-amber-900">
                          One update is waiting for your review
                        </p>
                        <Button
                          size="sm"
                          variant="secondary"
                          className="mt-2"
                          onClick={() => setWizard({ patient, report: openReport })}
                        >
                          <Eye className="h-4 w-4" aria-hidden />
                          Review it
                        </Button>
                      </div>
                    ) : null}

                    <div>
                      <div className="mb-2 flex items-center justify-between">
                        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                          Recent updates
                        </p>
                        <button
                          type="button"
                          onClick={() => router.push(`/patients/${patient.id}`)}
                          className="inline-flex items-center gap-1 text-xs font-medium text-brand-600 hover:text-brand-700"
                        >
                          Open patient <ArrowRight className="h-3.5 w-3.5" aria-hidden />
                        </button>
                      </div>
                      {reports.length === 0 ? (
                        <p className="text-sm text-muted">No updates recorded yet.</p>
                      ) : (
                        <ul className="space-y-1.5">
                          {reports.slice(0, 3).map((report) => (
                            <li key={report.id} className="flex items-center justify-between gap-2 text-sm">
                              <span className="truncate text-slate-700">
                                {REPORT_MODE_LABELS[report.mode] ?? report.mode}
                              </span>
                              <span className="shrink-0">
                                <Badge tone={statusToneForReport(report.status)}>
                                  {REPORT_STATUS_LABELS[report.status] ?? report.status}
                                </Badge>
                              </span>
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>

                    <div className="flex flex-wrap gap-2">
                      <Button size="sm" onClick={() => setWizard({ patient, mode: "QUICK_STATUS" })}>
                        <Plus className="h-4 w-4" aria-hidden />
                        Quick status
                      </Button>
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => setWizard({ patient, mode: "STRUCTURED" })}
                      >
                        Structured
                      </Button>
                      <Button size="sm" variant="secondary" onClick={() => setWizard({ patient, mode: "TEXT" })}>
                        Text
                      </Button>
                      <Button size="sm" variant="secondary" onClick={() => setWizard({ patient, mode: "VOICE" })}>
                        Voice
                      </Button>
                    </div>
                  </CardBody>
                </Card>
              );
            })}
          </div>
        </>
      )}

      {wizard ? (
        <ReportWizard
          patient={wizard.patient}
          presetReport={wizard.report}
          presetMode={wizard.mode}
          onClose={() => setWizard(null)}
          onSaved={() => setReloadToken((value) => value + 1)}
        />
      ) : null}
    </div>
  );
}

function statusToneForReport(status: string): "neutral" | "teal" | "amber" | "emerald" | "rose" {
  switch (status) {
    case "CONFIRMED":
      return "emerald";
    case "REVIEW_REQUIRED":
    case "PROCESSING":
      return "amber";
    case "CANCELLED":
      return "rose";
    case "DRAFT":
      return "neutral";
    default:
      return "neutral";
  }
}
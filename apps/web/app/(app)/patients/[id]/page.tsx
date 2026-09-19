"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Plus } from "lucide-react";
import { patientsApi } from "@/lib/api/patients";
import { reportsApi } from "@/lib/api/reports";
import { observationsApi, tasksApi, timelineApi, visitsApi } from "@/lib/api/records";
import { ApiErrorResponse } from "@/lib/api/client";
import type {
  CareGoal,
  CareGoalPriority,
  CareGoalStatus,
  CarePlanStatus,
  CareTask,
  CareTeamMember,
  ChangeItem,
  Observation,
  ObservationCreate,
  PatientDetail,
  TimelineItem,
  Visit,
} from "@/lib/api/types";
import { PageHeader } from "@/components/ui/page";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { StatusBadge, PriorityBadge } from "@/components/status-badge";
import { Badge } from "@/components/ui/badge";
import { Tabs } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Field, Input, Select, Textarea } from "@/components/ui/field";
import { EmptyState, PageLoader } from "@/components/ui/feedback";
import { useAuth } from "@/components/providers/auth-provider";
import {
  activityLabel,
  COMPARISON_LABELS,
  GENDER_LABELS,
  OBSERVATION_LABELS,
  RELATIONSHIP_LABELS,
  SOURCE_LABELS,
  TASK_TYPE_LABELS,
} from "@/lib/constants";
import { ageFrom, formatDate, formatDateTime, initials } from "@/lib/format";
import { cn } from "@/lib/cn";

type TabKey = "overview" | "observations" | "visits" | "tasks" | "timeline";

const OBSERVATION_TYPES = [
  "PAIN",
  "SLEEP",
  "FOOD_INTAKE",
  "MOBILITY",
  "MOOD",
  "BREATHING",
  "ENERGY",
  "OTHER",
];

export default function PatientDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const patientId = params.id;

  const [patient, setPatient] = useState<PatientDetail | null>(null);
  const [observations, setObservations] = useState<Observation[]>([]);
  const [visits, setVisits] = useState<Visit[]>([]);
  const [tasks, setTasks] = useState<CareTask[]>([]);
  const [timeline, setTimeline] = useState<TimelineItem[]>([]);
  const [timelineKind, setTimelineKind] = useState<string>("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<TabKey>("overview");
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      patientsApi().get(patientId),
      observationsApi().forPatient(patientId),
      visitsApi().forPatient(patientId),
      tasksApi().forPatient(patientId),
      timelineApi().forPatient(patientId, timelineKind === "all" ? undefined : timelineKind),
    ])
      .then(([detail, obs, vis, ts, tl]) => {
        if (cancelled) return;
        setPatient(detail);
        setObservations(obs.items);
        setVisits(vis.items);
        setTasks(ts.items);
        setTimeline(tl.items);
        setError(null);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err instanceof ApiErrorResponse ? err.message : "Unable to load this patient.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [patientId, timelineKind, reloadToken]);

  if (loading) return <PageLoader label="Loading patient…" />;
  if (error || !patient) {
    return (
      <EmptyState
        title="Patient unavailable"
        description={error ?? "This patient could not be found."}
        action={
          <Button variant="secondary" onClick={() => router.push("/patients")}>
            Back to patients
          </Button>
        }
      />
    );
  }

  const tabCounts: Record<Exclude<TabKey, "overview">, number> = {
    observations: observations.length,
    visits: visits.length,
    tasks: tasks.length,
    timeline: timeline.length,
  };

  return (
    <div className="space-y-6">
      <div>
        <button
          onClick={() => router.push("/patients")}
          className="mb-4 inline-flex items-center gap-1.5 text-sm text-muted hover:text-slate-700"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden />
          All patients
        </button>

        <PageHeader
          title={patient.full_name}
          description={`${ageFrom(patient.date_of_birth) ?? "—"} years · ${
            GENDER_LABELS[patient.gender ?? "UNSPECIFIED"] ?? patient.gender
          } · ${patient.preferred_language ?? "—"}${patient.phone ? ` · ${patient.phone}` : ""}`}
          actions={<StatusBadge value={patient.status} />}
        />
      </div>

      <Tabs
        tabs={[
          { key: "overview", label: "Overview" },
          { key: "observations", label: "Observations", count: tabCounts.observations },
          { key: "visits", label: "Visits", count: tabCounts.visits },
          { key: "tasks", label: "Tasks", count: tabCounts.tasks },
          { key: "timeline", label: "Timeline", count: tabCounts.timeline },
        ]}
        active={tab}
        onChange={(key) => setTab(key as TabKey)}
      />

      <div className="pt-2">
        {tab === "overview" && (
          <OverviewPanel
            key={patient.id}
            patient={patient}
            onRefresh={() => setReloadToken((value) => value + 1)}
          />
        )}
        {tab === "observations" && (
          <ObservationsPanel
            observations={observations}
            patientId={patientId}
            onRecorded={() => setReloadToken((value) => value + 1)}
          />
        )}
        {tab === "visits" && <VisitsPanel visits={visits} onRefresh={() => setReloadToken((value) => value + 1)} />}
        {tab === "tasks" && <TasksPanel tasks={tasks} onRefresh={() => setReloadToken((value) => value + 1)} />}
        {tab === "timeline" && (
          <TimelinePanel items={timeline} kind={timelineKind} onKindChange={setTimelineKind} />
        )}
      </div>
    </div>
  );
}

function OverviewPanel({
  patient,
  onRefresh,
}: {
  patient: PatientDetail;
  onRefresh: () => void;
}) {
  const { canAccess } = useAuth();
  const [planEditing, setPlanEditing] = useState(false);
  const [planStatus, setPlanStatus] = useState<CarePlanStatus | null>(null);
  const [planSummary, setPlanSummary] = useState("");
  const [goalAdding, setGoalAdding] = useState(false);
  const [goalTitle, setGoalTitle] = useState("");
  const [goalDescription, setGoalDescription] = useState("");
  const [goalPriority, setGoalPriority] = useState<CareGoalPriority>("NORMAL");
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  function openPlanEditing() {
    setPlanStatus(patient.care_plan?.status ?? null);
    setPlanSummary(patient.care_plan?.summary ?? "");
    setPlanEditing(true);
  }

  async function savePlan(event: React.FormEvent) {
    event.preventDefault();
    if (!patient.care_plan) return;
    setSaving(true);
    setFormError(null);
    try {
      await patientsApi().updateCarePlan(patient.id, {
        status: planStatus ?? undefined,
        summary: planSummary.trim() || null,
      });
      setPlanEditing(false);
      onRefresh();
    } catch (err) {
      setFormError(err instanceof ApiErrorResponse ? err.message : "Unable to save the care plan.");
    } finally {
      setSaving(false);
    }
  }

  async function saveGoal(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    setFormError(null);
    try {
      await patientsApi().createCareGoal(patient.id, {
        title: goalTitle.trim(),
        description: goalDescription.trim() || null,
        priority: goalPriority,
      });
      setGoalTitle("");
      setGoalDescription("");
      setGoalAdding(false);
      onRefresh();
    } catch (err) {
      setFormError(err instanceof ApiErrorResponse ? err.message : "Unable to add the goal.");
    } finally {
      setSaving(false);
    }
  }

  async function updateGoalStatus(goalId: string, status: CareGoalStatus) {
    setFormError(null);
    try {
      await patientsApi().updateCareGoal(patient.id, goalId, { status });
      onRefresh();
    } catch (err) {
      setFormError(err instanceof ApiErrorResponse ? err.message : "Unable to update the goal.");
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <RecentChangesCard patientId={patient.id} />

      <Card className="lg:col-span-2">
        <CardHeader title="About" description="Contact and address details" />
        <CardBody className="grid grid-cols-1 gap-x-6 gap-y-4 sm:grid-cols-2">
          <Detail label="Address" value={patient.address ?? "—"} />
          <Detail label="Emergency contact" value={patient.emergency_contact_name ?? "—"} />
          <Detail label="Emergency phone" value={patient.emergency_contact_phone ?? "—"} />
          <Detail label="Language" value={patient.preferred_language ?? "—"} />
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="Care team" />
        <CardBody className="pt-0">
          {patient.care_team.length === 0 ? (
            <p className="text-sm text-muted">No care team assigned.</p>
          ) : (
            <ul className="divide-y divide-line">
              {patient.care_team.map((member) => (
                <CareTeamRow key={member.user_id} member={member} />
              ))}
            </ul>
          )}
        </CardBody>
      </Card>

      <Card className="lg:col-span-2">
        <CardHeader title="Caregivers" />
        <CardBody className="pt-0">
          {patient.caregivers.length === 0 ? (
            <p className="text-sm text-muted">No caregivers linked yet.</p>
          ) : (
            <ul className="divide-y divide-line">
              {patient.caregivers.map((caregiver) => (
                <li key={caregiver.id} className="flex items-center justify-between py-2.5">
                  <span className="text-sm font-medium text-slate-800">{caregiver.full_name}</span>
                  <Badge tone={caregiver.is_primary ? "teal" : "neutral"}>
                    {RELATIONSHIP_LABELS[caregiver.relationship] ?? caregiver.relationship}
                    {caregiver.is_primary ? " · Primary" : ""}
                  </Badge>
                </li>
              ))}
            </ul>
          )}
        </CardBody>
      </Card>

      {planEditing ? (
        <Card className="lg:col-span-2">
          <CardHeader title="Edit care plan" />
          <CardBody className="pt-0">
            <form onSubmit={savePlan} className="space-y-4">
              <Field label="Status">
                <Select
                  value={planStatus ?? "ACTIVE"}
                  onChange={(event) => setPlanStatus(event.target.value as CarePlanStatus)}
                >
                  {CARE_PLAN_STATUSES.map((status) => (
                    <option key={status} value={status}>
                      {status.replaceAll("_", " ")}
                    </option>
                  ))}
                </Select>
              </Field>
              <Field label="Summary">
                <Textarea value={planSummary} onChange={(event) => setPlanSummary(event.target.value)} />
              </Field>
              {formError ? (
                <p className="text-sm text-rose-700" role="alert">{formError}</p>
              ) : null}
              <div className="flex items-center gap-2">
                <Button type="submit" disabled={saving}>{saving ? "Saving…" : "Save plan"}</Button>
                <Button variant="ghost" type="button" onClick={() => setPlanEditing(false)}>Cancel</Button>
              </div>
            </form>
          </CardBody>
        </Card>
      ) : (
        <Card className="lg:col-span-2">
          <CardHeader
            title="Care plan"
            action={
              patient.care_plan && canAccess("care_plan.update") ? (
                <Button size="sm" variant="ghost" onClick={openPlanEditing}>
                  Edit
                </Button>
              ) : undefined
            }
          />
          <CardBody className="pt-0">
            {patient.care_plan ? (
              <div className="space-y-2">
                <div className="flex items-center justify-between gap-3">
                  <StatusBadge value={patient.care_plan.status} />
                  <p className="text-xs text-muted">
                    Started {formatDate(patient.care_plan.start_date)} · review{" "}
                    {formatDate(patient.care_plan.review_date)}
                  </p>
                </div>
                <p className="text-sm text-slate-700">{patient.care_plan.summary ?? "No summary."}</p>
              </div>
            ) : (
              <EmptyState
                title="No care plan yet"
                description="A care plan has not been created for this patient."
              />
            )}
          </CardBody>
        </Card>
      )}

      <Card>
        <CardHeader
          title="Goals"
          action={
            canAccess("care_goal.create") ? (
              <Button size="sm" variant="ghost" onClick={() => setGoalAdding((value) => !value)}>
                Add goal
              </Button>
            ) : undefined
          }
        />
        <CardBody className="pt-0">
          {goalAdding ? (
            <form onSubmit={saveGoal} className="space-y-3 border-b border-line pb-4">
              <Field label="Title">
                <Input
                  value={goalTitle}
                  onChange={(event) => setGoalTitle(event.target.value)}
                  placeholder="e.g. Comfortable nights"
                />
              </Field>
              <Field label="Description">
                <Input
                  value={goalDescription}
                  onChange={(event) => setGoalDescription(event.target.value)}
                  placeholder="Optional"
                />
              </Field>
              <Field label="Priority">
                <Select
                  value={goalPriority}
                  onChange={(event) => setGoalPriority(event.target.value as CareGoalPriority)}
                >
                  {CARE_GOAL_PRIORITIES.map((priority) => (
                    <option key={priority} value={priority}>
                      {priority.charAt(0) + priority.slice(1).toLowerCase()}
                    </option>
                  ))}
                </Select>
              </Field>
              {formError ? (
                <p className="text-sm text-rose-700" role="alert">{formError}</p>
              ) : null}
              <div className="flex items-center gap-2">
                <Button type="submit" size="sm" disabled={saving || !goalTitle.trim()}>
                  {saving ? "Adding…" : "Add goal"}
                </Button>
                <Button variant="ghost" size="sm" type="button" onClick={() => setGoalAdding(false)}>
                  Cancel
                </Button>
              </div>
            </form>
          ) : null}
          {patient.care_goals.length === 0 ? (
            <p className="pt-3 text-sm text-muted">No goals recorded.</p>
          ) : (
            <ul className="space-y-2 pt-3">
              {patient.care_goals.map((goal) => (
                <GoalRow
                  key={goal.id}
                  goal={goal}
                  canEditStatus={canAccess("care_goal.update")}
                  onStatusChange={updateGoalStatus}
                />
              ))}
            </ul>
          )}
        </CardBody>
      </Card>

      <Card className="lg:col-span-3">
        <CardBody className="flex justify-end">
          <Button variant="secondary" onClick={onRefresh}>
            Refresh
          </Button>
        </CardBody>
      </Card>
    </div>
  );
}

const CARE_PLAN_STATUSES = ["DRAFT", "ACTIVE", "ON_HOLD", "COMPLETED", "ARCHIVED"] as const;
const CARE_GOAL_PRIORITIES = ["LOW", "NORMAL", "HIGH"] as const;
const CARE_GOAL_STATUSES = ["OPEN", "IN_PROGRESS", "ACHIEVED", "DROPPED"] as const;

function RecentChangesCard({ patientId }: { patientId: string }) {
  const [items, setItems] = useState<ChangeItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    reportsApi()
      .recentChanges(patientId)
      .then((result) => {
        if (!cancelled) setItems(result.items);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof ApiErrorResponse ? err.message : "Unable to load changes.");
      });
    return () => {
      cancelled = true;
    };
  }, [patientId]);

  return (
    <Card className="lg:col-span-3">
      <CardHeader
        title="Recent changes"
        description="How the latest recorded values compare to the previous entry."
      />
      <CardBody className="pt-0">
        {error ? (
          <p className="text-sm text-rose-700">{error}</p>
        ) : items === null ? (
          <p className="text-sm text-muted">Loading…</p>
        ) : items.length === 0 ? (
          <p className="text-sm text-muted">No recorded observations yet.</p>
        ) : (
          <ul className="divide-y divide-line">
            {items.map((item, index) => (
              <li key={`${item.type}-${index}`} className="flex items-center justify-between gap-4 py-3">
                <div className="min-w-0">
                  <p className="text-sm font-medium text-slate-800">
                    {OBSERVATION_LABELS[item.type] ?? item.type}
                  </p>
                  <p className="mt-0.5 text-xs text-muted">
                    {item.previous_observed_at
                      ? `Previous ${formatDateTime(item.previous_observed_at)}`
                      : "First recorded"}
                  </p>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  {item.previous_value ? (
                    <span className="text-xs text-muted line-through">
                      {item.previous_value}
                      {item.previous_unit ? ` ${item.previous_unit}` : ""}
                    </span>
                  ) : null}
                  <span className="text-sm font-medium text-slate-900">
                    {item.current_value}
                    {item.current_unit ? ` ${item.current_unit}` : ""}
                  </span>
                  <Badge tone={comparisonTone(item.comparison)}>
                    {COMPARISON_LABELS[item.comparison] ?? item.comparison}
                  </Badge>
                </div>
              </li>
            ))}
          </ul>
        )}
      </CardBody>
    </Card>
  );
}

function comparisonTone(comparison: string): "neutral" | "teal" | "amber" | "sky" | "violet" {
  switch (comparison) {
    case "increased":
      return "amber";
    case "decreased":
      return "sky";
    case "changed":
      return "violet";
    case "first":
      return "teal";
    default:
      return "neutral";
  }
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-0.5 text-sm text-slate-900">{value}</p>
    </div>
  );
}

function CareTeamRow({ member }: { member: CareTeamMember }) {
  return (
    <li className="flex items-center justify-between py-2.5">
      <div className="flex items-center gap-2.5 min-w-0">
        <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-slate-100 text-xs font-semibold text-slate-600">
          {initials(member.full_name)}
        </span>
        <div className="min-w-0">
          <p className="truncate text-sm font-medium text-slate-800">{member.full_name}</p>
          <p className="truncate text-xs text-muted">{member.email}</p>
        </div>
      </div>
      <Badge tone="neutral">{member.role.replaceAll("_", " ").toLowerCase()}</Badge>
    </li>
  );
}

function GoalRow({
  goal,
  canEditStatus,
  onStatusChange,
}: {
  goal: CareGoal;
  canEditStatus: boolean;
  onStatusChange: (goalId: string, status: CareGoalStatus) => void;
}) {
  return (
    <li className="rounded-md border border-line px-3 py-2">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm font-medium text-slate-800">{goal.title}</p>
          {goal.description ? <p className="mt-0.5 text-xs text-muted">{goal.description}</p> : null}
        </div>
        <div className="flex shrink-0 items-center gap-1.5">
          <PriorityBadge value={goal.priority} />
          {canEditStatus ? (
            <Select
              value={goal.status}
              onChange={(event) => onStatusChange(goal.id, event.target.value as CareGoalStatus)}
              className="w-auto py-1 text-xs"
              aria-label={`Status for ${goal.title}`}
            >
              {CARE_GOAL_STATUSES.map((status) => (
                <option key={status} value={status}>
                  {status.replaceAll("_", " ")}
                </option>
              ))}
            </Select>
          ) : (
            <StatusBadge value={goal.status} />
          )}
        </div>
      </div>
    </li>
  );
}

function ObservationsPanel({
  observations,
  patientId,
  onRecorded,
}: {
  observations: Observation[];
  patientId: string;
  onRecorded: () => void;
}) {
  const { canAccess } = useAuth();
  const [showForm, setShowForm] = useState(false);
  const [type, setType] = useState<ObservationCreate["type"]>("PAIN");
  const [value, setValue] = useState("");
  const [unit, setUnit] = useState("");
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function record(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await observationsApi().create({
        patient_id: patientId,
        type,
        value: value.trim() || null,
        unit: unit.trim() || null,
        notes: notes.trim() || null,
      });
      setValue("");
      setUnit("");
      setNotes("");
      setShowForm(false);
      onRecorded();
    } catch (err) {
      setError(err instanceof ApiErrorResponse ? err.message : "Unable to record observation.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card>
      <CardHeader
        title="Observations"
        description="Clinical and daily observations"
        action={
          canAccess("observation.create") ? (
            <Button size="sm" onClick={() => setShowForm((value) => !value)}>
              <Plus className="h-4 w-4" aria-hidden />
              Record
            </Button>
          ) : undefined
        }
      />

      {showForm ? (
        <CardBody className="border-t border-line pt-4">
          <form onSubmit={record} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Field label="Type">
              <Select value={type} onChange={(event) => setType(event.target.value as ObservationCreate["type"])}>
                {OBSERVATION_TYPES.map((obsType) => (
                  <option key={obsType} value={obsType}>
                    {OBSERVATION_LABELS[obsType] ?? obsType}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="Value">
              <Input value={value} onChange={(event) => setValue(event.target.value)} placeholder="e.g. 3" />
            </Field>
            <Field label="Unit">
              <Input value={unit} onChange={(event) => setUnit(event.target.value)} placeholder="e.g. /10" />
            </Field>
            <Field label="Notes">
              <Input value={notes} onChange={(event) => setNotes(event.target.value)} placeholder="Optional" />
            </Field>
            {error ? (
              <p className="text-sm text-rose-700 sm:col-span-2" role="alert">
                {error}
              </p>
            ) : null}
            <div className="flex items-center gap-2 sm:col-span-2 lg:col-span-4">
              <Button type="submit" disabled={saving}>
                {saving ? "Saving…" : "Save observation"}
              </Button>
              <Button variant="ghost" onClick={() => setShowForm(false)}>
                Cancel
              </Button>
            </div>
          </form>
        </CardBody>
      ) : null}

      {observations.length === 0 ? (
        <CardBody>
          <EmptyState title="No observations" description="Record the first observation above." />
        </CardBody>
      ) : (
        <CardBody className="pt-0">
          <ul className="divide-y divide-line">
            {observations.map((observation) => (
              <li key={observation.id} className="flex items-center justify-between gap-4 py-3">
                <div className="min-w-0">
                  <p className="text-sm font-medium text-slate-800">
                    {OBSERVATION_LABELS[observation.type] ?? observation.type}
                    {observation.value ? (
                      <span className="ml-1.5 text-slate-600">
                        {observation.value}
                        {observation.unit ? ` ${observation.unit}` : ""}
                      </span>
                    ) : null}
                  </p>
                  {observation.notes ? <p className="mt-0.5 text-xs text-muted">{observation.notes}</p> : null}
                </div>
                <div className="shrink-0 text-right">
                  <p className="text-xs text-muted">{formatDateTime(observation.observed_at)}</p>
                  <div className="mt-1 flex items-center justify-end gap-1">
                    {observation.ai_generated ? <Badge tone="violet">AI-assisted</Badge> : null}
                    {observation.human_verified ? <Badge tone="emerald">Verified</Badge> : null}
                    {observation.source ? (
                      <Badge tone="neutral">{SOURCE_LABELS[observation.source] ?? observation.source}</Badge>
                    ) : null}
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </CardBody>
      )}
    </Card>
  );
}

function VisitsPanel({ visits, onRefresh }: { visits: Visit[]; onRefresh: () => void }) {
  if (visits.length === 0) {
    return (
      <Card>
        <CardBody>
          <EmptyState title="No visits yet" description="Visits for this patient will appear here." />
        </CardBody>
      </Card>
    );
  }
  return (
    <Card>
      <CardBody className="pt-6">
        <ul className="divide-y divide-line">
          {visits.map((visit) => (
            <li key={visit.id} className="flex items-center justify-between gap-4 py-3">
              <div className="min-w-0">
                <p className="text-sm font-medium text-slate-800">{formatDateTime(visit.scheduled_at)}</p>
                {visit.notes ? <p className="mt-0.5 text-xs text-muted">{visit.notes}</p> : null}
              </div>
              <div className="flex shrink-0 items-center gap-3">
                <span className="text-xs text-muted">{visit.assigned_to_name ?? "Unassigned"}</span>
                <StatusBadge value={visit.status} />
              </div>
            </li>
          ))}
        </ul>
      </CardBody>
      <CardBody>
        <Button variant="secondary" size="sm" onClick={onRefresh}>
          Refresh
        </Button>
      </CardBody>
    </Card>
  );
}

function TasksPanel({ tasks, onRefresh }: { tasks: CareTask[]; onRefresh: () => void }) {
  if (tasks.length === 0) {
    return (
      <Card>
        <CardBody>
          <EmptyState title="No tasks" description="Tasks for this patient will appear here." />
        </CardBody>
      </Card>
    );
  }
  return (
    <Card>
      <CardBody className="pt-6">
        <ul className="divide-y divide-line">
          {tasks.map((task) => (
            <li key={task.id} className="flex items-center justify-between gap-4 py-3">
              <div className="min-w-0">
                <p className="text-sm font-medium text-slate-800">{task.title}</p>
                <p className="mt-0.5 text-xs text-muted">
                  {TASK_TYPE_LABELS[task.task_type] ?? task.task_type}
                  {task.due_at ? ` · due ${formatDate(task.due_at)}` : ""}
                </p>
              </div>
              <div className="flex shrink-0 items-center gap-1.5">
                <PriorityBadge value={task.priority} />
                <StatusBadge value={task.status} />
              </div>
            </li>
          ))}
        </ul>
      </CardBody>
      <CardBody>
        <Button variant="secondary" size="sm" onClick={onRefresh}>
          Refresh
        </Button>
      </CardBody>
    </Card>
  );
}

const KIND_DOT: Record<string, string> = {
  observation: "bg-amber-400",
  visit: "bg-brand-500",
  task: "bg-sky-400",
  communication: "bg-violet-400",
  caregiver_report: "bg-teal-400",
};

const TIMELINE_FILTERS = [
  { key: "all", label: "All" },
  { key: "observations", label: "Observations" },
  { key: "visits", label: "Visits" },
  { key: "tasks", label: "Tasks" },
  { key: "communications", label: "Communications" },
  { key: "caregiver_updates", label: "Caregiver updates" },
];

function TimelinePanel({
  items,
  kind,
  onKindChange,
}: {
  items: TimelineItem[];
  kind: string;
  onKindChange: (kind: string) => void;
}) {
  if (items.length === 0) {
    return (
      <Card>
        <CardBody>
          <EmptyState title="Nothing on record" description="Clinical activity will be listed here in time order." />
        </CardBody>
      </Card>
    );
  }
  return (
    <Card>
      <CardBody className="pt-4">
        <div className="mb-4 flex flex-wrap gap-1.5 overflow-x-auto">
          {TIMELINE_FILTERS.map((filter) => (
            <button
              key={filter.key}
              type="button"
              onClick={() => onKindChange(filter.key)}
              aria-pressed={kind === filter.key}
              className={cn(
                "rounded-full border px-3 py-1 text-xs font-medium transition-colors",
                kind === filter.key
                  ? "border-brand-200 bg-brand-50 text-brand-800"
                  : "border-line bg-white text-slate-600 hover:bg-slate-50",
              )}
            >
              {filter.label}
            </button>
          ))}
        </div>
        <ol className="space-y-0">
          {items.map((item, index) => (
            <li key={item.id} className="relative flex gap-4 pb-6">
              {index < items.length - 1 ? (
                <span className="absolute left-[5px] top-5 h-full w-px bg-line" aria-hidden />
              ) : null}
              <span
                className={cn(
                  "relative mt-1.5 h-[11px] w-[11px] shrink-0 rounded-full ring-2 ring-white",
                  KIND_DOT[item.kind] ?? "bg-slate-300",
                )}
                aria-hidden
              />
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-slate-800">{item.title}</p>
                {item.detail ? <p className="mt-0.5 text-xs text-muted">{item.detail}</p> : null}
                <p className="mt-0.5 text-xs text-slate-400">{formatDateTime(item.at)}</p>
              </div>
              <Badge tone="neutral" className="shrink-0 self-start">
                {activityLabel(item.kind)}
              </Badge>
            </li>
          ))}
        </ol>
      </CardBody>
    </Card>
  );
}
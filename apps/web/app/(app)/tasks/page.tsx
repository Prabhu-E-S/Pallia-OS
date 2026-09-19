"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Plus } from "lucide-react";
import { tasksApi } from "@/lib/api/records";
import { patientsApi } from "@/lib/api/patients";
import { ApiErrorResponse } from "@/lib/api/client";
import type {
  CareTask,
  CareTaskPriority,
  CareTaskStatus,
  CareTaskType,
  PatientSummary,
} from "@/lib/api/types";
import { PageHeader } from "@/components/ui/page";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { Table } from "@/components/ui/table";
import { StatusBadge, PriorityBadge } from "@/components/status-badge";
import { EmptyState, PageLoader } from "@/components/ui/feedback";
import { Button } from "@/components/ui/button";
import { Field, Input, Select, Textarea } from "@/components/ui/field";
import { formatDate } from "@/lib/format";
import { PRIORITY_LABELS, STATUS_LABELS, TASK_TYPE_LABELS } from "@/lib/constants";

const STATUS_FILTERS = [
  { value: "", label: "All statuses" },
  ...Object.entries(STATUS_LABELS).map(([value, label]) => ({ value, label })),
].filter((option) =>
  ["CREATED", "ASSIGNED", "ACCEPTED", "IN_PROGRESS", "COMPLETED", "VERIFIED", "CANCELLED"].includes(
    option.value,
  ),
);

const PRIORITIES: CareTaskPriority[] = ["LOW", "NORMAL", "HIGH", "URGENT"];
const TYPES: CareTaskType[] = [
  "GENERAL",
  "FOLLOWUP",
  "SCHEDULING",
  "COMMUNICATION",
  "LOGISTICS",
  "ADMINISTRATIVE",
];

export default function TasksPage() {
  const router = useRouter();
  const [items, setItems] = useState<CareTask[]>([]);
  const [patients, setPatients] = useState<PatientSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      tasksApi().list({ status: status || undefined }),
      patientsApi().list({ status: "ACTIVE" }),
    ])
      .then(([tasks, people]) => {
        if (cancelled) return;
        setItems(tasks.items);
        setPatients(people.items);
        setError(null);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err instanceof ApiErrorResponse ? err.message : "Unable to load tasks.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [status, reloadToken]);

  const rows = items.map((task) => ({
    key: task.id,
    title: (
      <div>
        <p className="font-medium text-slate-900">{task.title}</p>
        {task.description ? <p className="mt-0.5 line-clamp-1 text-xs text-muted">{task.description}</p> : null}
      </div>
    ),
    patient: (
      <button
        onClick={() => router.push(`/patients/${task.patient_id}`)}
        className="text-sm font-medium text-brand-800 hover:underline"
      >
        {task.patient_name ?? "Patient"}
      </button>
    ),
    type: TASK_TYPE_LABELS[task.task_type] ?? task.task_type,
    priority: <PriorityBadge value={task.priority} />,
    due: formatDate(task.due_at),
    assigned: task.assigned_to_name ?? "—",
    status: <StatusBadge value={task.status} />,
  }));

  return (
    <div className="space-y-6">
      <PageHeader
        title="Tasks"
        description="Open work across the care team"
        actions={
          <Button onClick={() => setShowForm((value) => !value)}>
            <Plus className="h-4 w-4" aria-hidden />
            New task
          </Button>
        }
      />

      {showForm ? (
        <TaskForm patients={patients} onCreated={() => { setShowForm(false); setReloadToken((value) => value + 1); }} />
      ) : null}

      <div className="flex w-56">
        <Field label="Status">
          <Select
            value={status}
            onChange={(event) => setStatus(event.target.value as CareTaskStatus | "")}
            aria-label="Filter tasks"
          >
            {STATUS_FILTERS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>
        </Field>
      </div>

      <div>
        {loading ? (
          <PageLoader label="Loading tasks…" />
        ) : error ? (
          <EmptyState title="Something went wrong" description={error} />
        ) : (
          <Table
            columns={[
              { key: "title", header: "Task" },
              { key: "patient", header: "Patient" },
              { key: "type", header: "Type" },
              { key: "priority", header: "Priority" },
              { key: "due", header: "Due" },
              { key: "assigned", header: "Assigned to" },
              { key: "status", header: "Status" },
            ]}
            rows={rows}
            rowKey={(row) => String(row.key)}
            empty={<EmptyState title="No tasks" description="Create a task to get started." />}
          />
        )}
      </div>
    </div>
  );
}

function TaskForm({
  patients,
  onCreated,
}: {
  patients: PatientSummary[];
  onCreated: () => void;
}) {
  const [patientId, setPatientId] = useState(patients[0]?.id ?? "");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [type, setType] = useState<CareTaskType>("GENERAL");
  const [priority, setPriority] = useState<CareTaskPriority>("NORMAL");
  const [due, setDue] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!patientId || !title.trim()) return;
    setSaving(true);
    setError(null);
    try {
      await tasksApi().create({
        patient_id: patientId,
        title: title.trim(),
        description: description.trim() || null,
        task_type: type,
        priority,
        due_at: due ? new Date(due).toISOString() : null,
      });
      setTitle("");
      setDescription("");
      onCreated();
    } catch (err) {
      setError(err instanceof ApiErrorResponse ? err.message : "Unable to create task.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card>
      <CardHeader title="Create a task" description="Assign follow-up work for a patient" />
      <CardBody>
        <form onSubmit={submit} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Field label="Patient" htmlFor="task-patient">
            <Select id="task-patient" value={patientId} onChange={(event) => setPatientId(event.target.value)} required>
              {patients.map((patient) => (
                <option key={patient.id} value={patient.id}>
                  {patient.full_name}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Title" htmlFor="task-title" className="sm:col-span-2">
            <Input
              id="task-title"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="e.g. Follow up on pain medication"
              required
            />
          </Field>
          <Field label="Due" htmlFor="task-due" hint="Optional">
            <Input id="task-due" type="datetime-local" value={due} onChange={(event) => setDue(event.target.value)} />
          </Field>
          <Field label="Type">
            <Select value={type} onChange={(event) => setType(event.target.value as CareTaskType)}>
              {TYPES.map((taskType) => (
                <option key={taskType} value={taskType}>
                  {TASK_TYPE_LABELS[taskType] ?? taskType}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Priority">
            <Select value={priority} onChange={(event) => setPriority(event.target.value as CareTaskPriority)}>
              {PRIORITIES.map((value) => (
                <option key={value} value={value}>
                  {PRIORITY_LABELS[value] ?? value}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Description" htmlFor="task-description" className="sm:col-span-2">
            <Textarea
              id="task-description"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="What needs to happen?"
            />
          </Field>
          {error ? (
            <p className="text-sm text-rose-700 sm:col-span-2" role="alert">
              {error}
            </p>
          ) : null}
          <div className="flex items-center gap-2 sm:col-span-2 lg:col-span-4">
            <Button type="submit" disabled={saving || patients.length === 0}>
              {saving ? "Creating…" : "Create task"}
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
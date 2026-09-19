"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/components/providers/auth-provider";
import { dashboardApi } from "@/lib/api/patients";
import { ApiErrorResponse } from "@/lib/api/client";
import type { ActivityItem, CareTask, DashboardSummary, Visit } from "@/lib/api/types";
import { PageHeader, StatCard } from "@/components/ui/page";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { StatusBadge, PriorityBadge } from "@/components/status-badge";
import { EmptyState, PageLoader } from "@/components/ui/feedback";
import { formatDateTime, formatTime } from "@/lib/format";
import { activityLabel, TASK_TYPE_LABELS } from "@/lib/constants";

function FailurePanel({ message }: { message: string }) {
  return (
    <Card>
      <CardBody className="py-10">
        <p className="text-center text-sm text-rose-700">{message}</p>
      </CardBody>
    </Card>
  );
}

export default function DashboardPage() {
  const { session } = useAuth();
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    dashboardApi()
      .summary()
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(
            err instanceof ApiErrorResponse ? err.message : "Unable to load the dashboard.",
          );
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (error) return <FailurePanel message={error} />;
  if (!data) return <PageLoader label="Loading overview…" />;

  const org = session?.user?.organization_name;

  return (
    <div className="space-y-8">
      <PageHeader
        title="Good to see you"
        description={org ? `${org} · today's overview` : "Today's overview"}
      />

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Patients" value={data.counts.patients} />
        <StatCard label="Active care plans" value={data.counts.active_care_plans} />
        <StatCard label="Visits today" value={data.counts.today_visits} />
        <StatCard label="Open tasks" value={data.counts.open_tasks} />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <TodayVisits visits={data.today_visits} />
        <OpenTasks tasks={data.open_tasks} />
      </div>

      <RecentActivity items={data.recent_activity} />
    </div>
  );
}

function TodayVisits({ visits }: { visits: Visit[] }) {
  if (visits.length === 0) {
    return (
      <Card>
        <CardHeader title="Visits today" />
        <CardBody>
          <EmptyState title="No visits scheduled" description="Nothing planned for today yet." />
        </CardBody>
      </Card>
    );
  }
  return (
    <Card>
      <CardHeader title="Visits today" action={<Link className="text-xs font-medium text-brand-700 hover:underline" href="/visits">All visits</Link>} />
      <CardBody className="space-y-1">
        {visits.map((visit) => (
          <Link
            key={visit.id}
            href={`/patients/${visit.patient_id}`}
            className="flex items-center justify-between gap-3 rounded-md px-2 py-2 hover:bg-slate-50"
          >
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-slate-800">
                {visit.patient_name ?? "Patient"}
              </p>
              <p className="text-xs text-muted">
                {formatTime(visit.scheduled_at)} · {visit.assigned_to_name ?? "Unassigned"}
              </p>
            </div>
            <StatusBadge value={visit.status} />
          </Link>
        ))}
      </CardBody>
    </Card>
  );
}

function OpenTasks({ tasks }: { tasks: CareTask[] }) {
  if (tasks.length === 0) {
    return (
      <Card>
        <CardHeader title="Open tasks" />
        <CardBody>
          <EmptyState title="No open tasks" description="Every task is settled. Well done." />
        </CardBody>
      </Card>
    );
  }
  return (
    <Card>
      <CardHeader title="Open tasks" action={<Link className="text-xs font-medium text-brand-700 hover:underline" href="/tasks">All tasks</Link>} />
      <CardBody className="space-y-1">
        {tasks.map((task) => (
          <Link
            key={task.id}
            href={`/patients/${task.patient_id}`}
            className="flex items-center justify-between gap-3 rounded-md px-2 py-2 hover:bg-slate-50"
          >
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-slate-800">{task.title}</p>
              <p className="text-xs text-muted">
                {task.patient_name ?? "Patient"} · {TASK_TYPE_LABELS[task.task_type] ?? task.task_type}
              </p>
            </div>
            <div className="flex shrink-0 items-center gap-1.5">
              <PriorityBadge value={task.priority} />
              <StatusBadge value={task.status} />
            </div>
          </Link>
        ))}
      </CardBody>
    </Card>
  );
}

function RecentActivity({ items }: { items: ActivityItem[] }) {
  return (
    <Card>
      <CardHeader title="Recent activity" />
      {items.length === 0 ? (
        <CardBody>
          <EmptyState title="Nothing recorded yet" description="Care activity will appear here." />
        </CardBody>
      ) : (
        <CardBody className="pt-0">
          <ul className="divide-y divide-line">
            {items.map((item) => (
              <RecentActivityRow key={item.id} item={item} />
            ))}
          </ul>
        </CardBody>
      )}
    </Card>
  );
}

function RecentActivityRow({ item }: { item: ActivityItem }) {
  const target = item.patient_id ? `/patients/${item.patient_id}` : null;
  const body = (
    <div className="flex items-center gap-3 py-3">
      <Badge tone="teal" className="shrink-0">
        {activityLabel(item.kind)}
      </Badge>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm text-slate-800">{item.title}</p>
        <p className="truncate text-xs text-muted">{item.patient_name ?? "—"}</p>
      </div>
      <span className="shrink-0 text-xs text-muted">{formatDateTime(item.at)}</span>
    </div>
  );
  return <li>{target ? <Link href={target} className="block hover:bg-slate-50 px-2">{body}</Link> : body}</li>;
}
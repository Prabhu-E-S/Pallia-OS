import { Badge } from "@/components/ui/badge";
import { PRIORITY_LABELS, STATUS_LABELS, statusTone } from "@/lib/constants";

export function StatusBadge({ value }: { value: string }) {
  return <Badge tone={statusTone(value)}>{STATUS_LABELS[value] ?? value}</Badge>;
}

export function PriorityBadge({ value }: { value: string }) {
  return <Badge tone={statusTone(value)}>{PRIORITY_LABELS[value] ?? value}</Badge>;
}
import type { Priority, Status } from "@/types";
import { STATUS_LABELS } from "@/lib/format";

// Colour is supplementary: every badge always shows its text label.
const STATUS_STYLES: Record<Status, string> = {
  OPEN: "bg-blue-50 text-blue-800 ring-blue-600/20",
  ASSIGNED: "bg-indigo-50 text-indigo-800 ring-indigo-600/20",
  IN_PROGRESS: "bg-amber-50 text-amber-900 ring-amber-600/25",
  RESOLVED: "bg-emerald-50 text-emerald-800 ring-emerald-600/20",
  REOPENED: "bg-orange-50 text-orange-900 ring-orange-600/25",
  CLOSED: "bg-slate-100 text-slate-700 ring-slate-500/20",
};
const STATUS_DOT: Record<Status, string> = {
  OPEN: "bg-blue-500",
  ASSIGNED: "bg-indigo-500",
  IN_PROGRESS: "bg-amber-500",
  RESOLVED: "bg-emerald-500",
  REOPENED: "bg-orange-500",
  CLOSED: "bg-slate-400",
};
const PRIORITY_STYLES: Record<Priority, string> = {
  LOW: "bg-slate-50 text-slate-700 ring-slate-400/30",
  MEDIUM: "bg-sky-50 text-sky-800 ring-sky-600/20",
  HIGH: "bg-orange-50 text-orange-900 ring-orange-600/25",
  URGENT: "bg-red-50 text-red-800 ring-red-600/25",
};
const PRIORITY_DOT: Record<Priority, string> = {
  LOW: "bg-slate-400",
  MEDIUM: "bg-sky-500",
  HIGH: "bg-orange-500",
  URGENT: "bg-red-500",
};
const base = "inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2.5 py-1 text-xs font-semibold leading-none ring-1 ring-inset";

export function StatusBadge({ status }: { status: Status }) {
  return (
    <span className={`${base} ${STATUS_STYLES[status]}`}>
      <span aria-hidden className={`h-1.5 w-1.5 rounded-full ${STATUS_DOT[status]}`} />
      <span className="font-normal opacity-70">Status:</span> {STATUS_LABELS[status]}
    </span>
  );
}

export function PriorityBadge({ priority, label }: { priority: Priority; label?: string }) {
  const text = label ?? priority.charAt(0) + priority.slice(1).toLowerCase();
  return (
    <span className={`${base} ${PRIORITY_STYLES[priority]}`}>
      <span aria-hidden className={`h-1.5 w-1.5 rounded-sm rotate-45 ${PRIORITY_DOT[priority]}`} />
      <span className="font-normal opacity-70">Priority:</span> {text}
    </span>
  );
}

export function OverdueBadge() {
  return (
    <span className={`${base} bg-red-600 text-white ring-red-700/40`}>
      <span aria-hidden className="h-1.5 w-1.5 animate-pulse rounded-full bg-white" />
      Overdue
    </span>
  );
}
import type { Role, Status } from "@/types";

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "-";
  return new Intl.DateTimeFormat("en-IN", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export const STATUS_LABELS: Record<Status, string> = {
  OPEN: "Open",
  ASSIGNED: "Assigned",
  IN_PROGRESS: "In progress",
  RESOLVED: "Resolved",
  REOPENED: "Reopened",
  CLOSED: "Closed",
};

export function roleHome(role: Role): string {
  switch (role) {
    case "STUDENT": return "/student";
    case "MAINTENANCE_STAFF": return "/staff";
    default: return "/manager"; // managers and administrators
  }
}

export function ticketListPath(role: Role): string {
  return `${roleHome(role)}/tickets`;
}

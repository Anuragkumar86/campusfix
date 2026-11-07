export type Role = "STUDENT" | "MAINTENANCE_STAFF" | "DEPARTMENT_MANAGER" | "ADMINISTRATOR";
export type Status = "OPEN" | "ASSIGNED" | "IN_PROGRESS" | "RESOLVED" | "REOPENED" | "CLOSED";
export type Priority = "LOW" | "MEDIUM" | "HIGH" | "URGENT";

export interface User {
  id: number;
  email: string;
  name: string;
  first_name: string;
  last_name: string;
  role: Role;
  role_label: string;
  department: { id: number; name: string } | null;
}

export interface UserBrief { id: number; name: string; role?: Role }
export interface Department { id: number; name: string; description: string }
export interface Category { id: number; name: string; description: string; department: { id: number; name: string } }

export interface TicketSummary {
  id: number;
  ticket_number: string;
  title: string;
  status: Status;
  status_label: string;
  priority: Priority;
  priority_label: string;
  category: { id: number; name: string };
  department: { id: number; name: string };
  building: string;
  floor: string;
  room_or_area: string;
  reporter: UserBrief;
  assigned_to: UserBrief | null;
  response_due_at: string | null;
  resolution_due_at: string | null;
  is_overdue: boolean;
  created_at: string;
  updated_at: string;
}

export interface Attachment {
  id: number;
  original_filename: string;
  content_type: string;
  file_size: number;
  uploaded_by: UserBrief;
  uploaded_at: string;
  url: string;
}
export interface Comment { id: number; author: UserBrief; message: string; created_at: string }
export interface HistoryEvent {
  id: number;
  event_type: string;
  event_label: string;
  old_value: string | null;
  new_value: string | null;
  note: string;
  changed_by: UserBrief;
  created_at: string;
}
export interface AssignmentRecord {
  id: number;
  assigned_to: UserBrief;
  assigned_by: UserBrief;
  assignment_note: string;
  assigned_at: string;
  is_active: boolean;
  unassigned_at: string | null;
}
export interface TicketPermissions {
  can_comment: boolean;
  can_attach: boolean;
  can_assign: boolean;
  can_set_priority: boolean;
  can_edit: boolean;
  available_transitions: Status[];
}
export interface TicketDetail extends TicketSummary {
  description: string;
  resolution_note: string;
  first_response_at: string | null;
  resolved_at: string | null;
  closed_at: string | null;
  attachments: Attachment[];
  comments: Comment[];
  history: HistoryEvent[];
  assignments: AssignmentRecord[];
  permissions: TicketPermissions;
}

export interface Paginated<T> { count: number; next: string | null; previous: string | null; results: T[] }

export interface DashboardSummary {
  role: Role;
  total: number;
  by_status?: Record<Status, number>;
  by_priority?: Record<Priority, number>;
  open_count?: number;
  in_progress?: number;
  resolved_or_closed?: number;
  assigned?: number;
  overdue?: number;
  due_soon?: number;
  due_soon_hours?: number;
  unassigned?: number;
  avg_resolution_hours?: number | null;
  resolved_sample_size?: number;
  department?: { id: number; name: string } | null;
  by_department?: { id: number; name: string; tickets_total: number; tickets_open: number }[];
  recent?: TicketSummary[];
  recently_completed?: TicketSummary[];
}
export interface CategoryCount { category_id: number; category: string; count: number }
export interface StaffMember { id: number; name: string }

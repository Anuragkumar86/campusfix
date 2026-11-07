"use client";

import Link from "next/link";
import { useState, type ReactNode } from "react";
import { api, API_BASE, ApiError, errorMessage } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { formatDateTime, formatFileSize, STATUS_LABELS, ticketListPath } from "@/lib/format";
import { useApiData } from "@/lib/useApi";
import { validateImage, validateRequiredNote } from "@/lib/validators";
import type { Priority, StaffMember, Status, TicketDetail as Ticket } from "@/types";
import { OverdueBadge, PriorityBadge, StatusBadge } from "./Badges";
import { ConfirmDialog } from "./ConfirmDialog";
import { EmptyState, ErrorBanner, SuccessBanner, Spinner } from "./Feedback";
import { FormField } from "./FormField";
import { Icon, type IconName } from "./Icons";
import { btnPrimary, btnSecondary, card, fileCls, inputCls } from "./ui";

interface Action { label: string; noteLabel: string; noteRequired: boolean; confirm?: string; danger?: boolean }
const ACTIONS: Partial<Record<Status, Action>> = {
  IN_PROGRESS: { label: "Start work", noteLabel: "Note (optional)", noteRequired: false },
  RESOLVED: { label: "Mark as resolved", noteLabel: "Resolution note", noteRequired: true },
  CLOSED: { label: "Accept resolution and close", noteLabel: "Note (optional)", noteRequired: false, confirm: "Closing confirms the issue is fixed. Only a manager can reopen it afterwards." },
  REOPENED: { label: "Reopen ticket", noteLabel: "Reason for reopening", noteRequired: true, confirm: "The ticket will return to the manager for re-assignment." },
  OPEN: { label: "Remove assignment", noteLabel: "Reason (optional)", noteRequired: false, confirm: "The ticket will become unassigned and return to the open queue.", danger: true },
};

function CardTitle({ id, icon, children }: { id: string; icon: IconName; children: ReactNode }) {
  return (
    <h2 id={id} className="mb-5 flex items-center gap-2.5 text-[15px] font-semibold text-slate-900">
      <span aria-hidden className="grid h-7 w-7 place-items-center rounded-lg bg-brand-50 text-brand-600"><Icon name={icon} className="h-4 w-4" /></span>
      {children}
    </h2>
  );
}

const panel = `p-5 sm:p-6 ${card}`;

export function TicketDetail({ id }: { id: string }) {
  const { user } = useAuth();
  const { data: ticket, error, loading, reload } = useApiData<Ticket>(`/api/tickets/${id}/`);
  const [notice, setNotice] = useState<string | null>(null);

  if (!user) return null;
  const backPath = ticketListPath(user.role);

  if (loading && !ticket) return <Spinner label="Loading ticket..." />;
  if (error) {
    const message = error.kind === "not_found"
      ? "This ticket does not exist or you do not have access to it."
      : error.message;
    return (
      <div className="space-y-4">
        <ErrorBanner message={message} onRetry={error.kind === "not_found" ? undefined : reload} />
        <Link href={backPath} className={btnSecondary}>Back to tickets</Link>
      </div>
    );
  }
  if (!ticket) return null;
  const p = ticket.permissions;
  const done = (msg: string) => { setNotice(msg); reload(); };

  return (
    <div>
      <Link href={backPath} className="group inline-flex items-center gap-1.5 text-sm font-semibold text-slate-500 transition hover:text-brand-700">
        <Icon name="arrow-left" className="h-4 w-4 transition group-hover:-translate-x-0.5" />
        Back to tickets
      </Link>

      <header className={`relative mb-6 mt-4 overflow-hidden p-5 sm:mb-8 sm:p-8 ${card}`}>
        <div aria-hidden className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-brand-400 via-brand-600 to-indigo-500" />
        <div aria-hidden className="pointer-events-none absolute -right-16 -top-20 h-56 w-56 rounded-full bg-brand-100/80 blur-3xl" />
        <p className="relative inline-block rounded-md bg-brand-50 px-2 py-1 font-mono text-xs font-semibold tracking-wide text-brand-700 ring-1 ring-inset ring-brand-100">{ticket.ticket_number}</p>
        <h1 className="relative mt-3 text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">{ticket.title}</h1>
        <div className="relative mt-4 flex flex-wrap gap-2">
          <StatusBadge status={ticket.status} />
          <PriorityBadge priority={ticket.priority} label={ticket.priority_label} />
          {ticket.is_overdue && <OverdueBadge />}
        </div>
      </header>

      {notice && <div className="mb-5"><SuccessBanner>{notice}</SuccessBanner></div>}

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="min-w-0 space-y-6 lg:col-span-2">
          <section className={panel} aria-labelledby="desc-h">
            <CardTitle id="desc-h" icon="list">Description</CardTitle>
            <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-700">{ticket.description}</p>
            {ticket.resolution_note && (
              <div className="mt-6 rounded-2xl bg-emerald-50 p-4 text-sm ring-1 ring-inset ring-emerald-200">
                <p className="flex items-center gap-2 font-semibold text-emerald-900"><Icon name="check" className="h-4 w-4" />Resolution note</p>
                <p className="mt-1.5 whitespace-pre-wrap leading-relaxed text-emerald-900">{ticket.resolution_note}</p>
              </div>
            )}
          </section>

          <Attachments ticket={ticket} onDone={done} />
          <Comments ticket={ticket} onDone={done} />
          <History ticket={ticket} />
        </div>

        <aside className="min-w-0 space-y-6" aria-label="Ticket details and actions">
          <section className={panel} aria-labelledby="det-h">
            <CardTitle id="det-h" icon="layers">Details</CardTitle>
            <dl className="space-y-3.5 text-sm">
              <Row label="Category">{ticket.category.name}</Row>
              <Row label="Department">{ticket.department.name}</Row>
              <Row label="Location">{[ticket.building, ticket.floor && `Floor ${ticket.floor}`, ticket.room_or_area].filter(Boolean).join(", ")}</Row>
              <Row label="Reported by">{ticket.reporter.name}</Row>
              <Row label="Assigned to">{ticket.assigned_to?.name ?? "Not assigned yet"}</Row>
              <Row label="Created">{formatDateTime(ticket.created_at)}</Row>
              <Row label="First response due">{formatDateTime(ticket.response_due_at)}</Row>
              <Row label="Resolution due">{formatDateTime(ticket.resolution_due_at)}</Row>
              {ticket.resolved_at && <Row label="Resolved">{formatDateTime(ticket.resolved_at)}</Row>}
              {ticket.closed_at && <Row label="Closed">{formatDateTime(ticket.closed_at)}</Row>}
            </dl>
          </section>

          {p.available_transitions.length > 0 && <StatusActions ticket={ticket} onDone={done} />}
          {p.can_set_priority && <PriorityPanel ticket={ticket} onDone={done} />}
          {p.can_assign && <AssignPanel ticket={ticket} onDone={done} />}
          {ticket.assignments.length > 0 && <AssignmentTrail ticket={ticket} />}
        </aside>
      </div>
    </div>
  );
}

function Row({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex justify-between gap-4 border-b border-slate-100 pb-3.5 last:border-0 last:pb-0">
      <dt className="shrink-0 text-slate-500">{label}</dt>
      <dd className="text-right font-medium text-slate-900">{children}</dd>
    </div>
  );
}

/* ------------------------------------------------------------- status actions */
function StatusActions({ ticket, onDone }: { ticket: Ticket; onDone: (m: string) => void }) {
  const [pending, setPending] = useState<Status | null>(null);
  const [note, setNote] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  const action = pending ? ACTIONS[pending] : undefined;

  function begin(status: Status) { setPending(status); setNote(""); setError(null); }
  function cancel() { setPending(null); setConfirming(false); setError(null); }

  function submit() {
    if (!pending || !action) return;
    if (action.noteRequired) {
      const problem = validateRequiredNote(note, action.noteLabel);
      if (problem) return setError(problem);
    }
    if (action.confirm) setConfirming(true);
    else void run();
  }

  async function run() {
    if (!pending) return;
    setBusy(true);
    setError(null);
    try {
      await api(`/api/tickets/${ticket.id}/status/`, { method: "POST", json: { status: pending, note } });
      const label = STATUS_LABELS[pending];
      cancel();
      onDone(`Ticket status updated to "${label}".`);
    } catch (e) {
      setConfirming(false);
      setError(e instanceof ApiError && e.fields.note ? e.fields.note : errorMessage(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className={`relative overflow-hidden p-5 sm:p-6 ${card} bg-gradient-to-b from-brand-50/70 to-white`} aria-labelledby="act-h">
      <div aria-hidden className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-brand-400 to-brand-600" />
      <CardTitle id="act-h" icon="bolt">Update progress</CardTitle>
      {!pending ? (
        <div className="flex flex-col gap-2.5">
          {ticket.permissions.available_transitions.map((s) => ACTIONS[s] && (
            <button key={s} type="button" className={ACTIONS[s]!.danger ? btnSecondary : btnPrimary} onClick={() => begin(s)}>
              {ACTIONS[s]!.label}
            </button>
          ))}
        </div>
      ) : (
        <form onSubmit={(e) => { e.preventDefault(); submit(); }} noValidate className="animate-fade-in space-y-4">
          <FormField id="status-note" label={action!.noteLabel} required={action!.noteRequired} error={error ?? undefined}>
            <textarea id="status-note" className={inputCls(!!error)} rows={3} value={note} maxLength={2000} onChange={(e) => setNote(e.target.value)} aria-invalid={!!error} />
          </FormField>
          <div className="flex flex-wrap gap-2">
            <button type="submit" className={btnPrimary} disabled={busy}>{action!.label}</button>
            <button type="button" className={btnSecondary} onClick={cancel} disabled={busy}>Cancel</button>
          </div>
        </form>
      )}
      <ConfirmDialog open={confirming} title={action?.label ?? ""} message={action?.confirm ?? ""} confirmLabel="Yes, continue" danger={action?.danger} busy={busy} onConfirm={run} onCancel={() => setConfirming(false)} />
    </section>
  );
}

/* ------------------------------------------------------------------- priority */
function PriorityPanel({ ticket, onDone }: { ticket: Ticket; onDone: (m: string) => void }) {
  const [priority, setPriority] = useState<Priority>(ticket.priority);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function save() {
    setBusy(true);
    setError(null);
    try {
      await api(`/api/tickets/${ticket.id}/priority/`, { method: "POST", json: { priority } });
      onDone("Priority updated and deadlines recalculated.");
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className={panel} aria-labelledby="prio-h">
      <CardTitle id="prio-h" icon="alert">Priority</CardTitle>
      <FormField id="prio" label="Set priority" error={error ?? undefined}>
        <select id="prio" className={inputCls(!!error)} value={priority} onChange={(e) => setPriority(e.target.value as Priority)}>
          {(["LOW", "MEDIUM", "HIGH", "URGENT"] as Priority[]).map((p) => <option key={p} value={p}>{p.charAt(0) + p.slice(1).toLowerCase()}</option>)}
        </select>
      </FormField>
      <button type="button" className={`${btnPrimary} mt-4 w-full`} onClick={save} disabled={busy || priority === ticket.priority}>
        {busy ? "Saving..." : "Save priority"}
      </button>
    </section>
  );
}

/* ------------------------------------------------------------------ assignment */
function AssignPanel({ ticket, onDone }: { ticket: Ticket; onDone: (m: string) => void }) {
  const staff = useApiData<StaffMember[]>("/api/staff/eligible/", { department: ticket.department.id });
  const [assignee, setAssignee] = useState("");
  const [note, setNote] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  const reassign = !!ticket.assigned_to;
  const options = (staff.data ?? []).filter((s) => s.id !== ticket.assigned_to?.id);
  const chosen = options.find((s) => String(s.id) === assignee);

  function submit() {
    if (!assignee) return setError("Select a staff member.");
    setError(null);
    if (reassign) setConfirming(true);
    else void run();
  }

  async function run() {
    setBusy(true);
    setError(null);
    try {
      await api(`/api/tickets/${ticket.id}/assignments/`, { method: "POST", json: { assigned_to: Number(assignee), note } });
      setConfirming(false);
      setAssignee("");
      setNote("");
      onDone(`Ticket ${reassign ? "reassigned" : "assigned"} to ${chosen?.name ?? "staff member"}.`);
    } catch (e) {
      setConfirming(false);
      setError(e instanceof ApiError && e.fields.assigned_to ? e.fields.assigned_to : errorMessage(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className={panel} aria-labelledby="asg-h">
      <CardTitle id="asg-h" icon="user">{reassign ? "Reassign ticket" : "Assign ticket"}</CardTitle>
      {staff.loading && <Spinner label="Loading staff..." />}
      {staff.error && <ErrorBanner message={staff.error.message} onRetry={staff.reload} />}
      {staff.data && options.length === 0 && <p className="text-sm text-slate-500">No other eligible staff in this department.</p>}
      {staff.data && options.length > 0 && (
        <form onSubmit={(e) => { e.preventDefault(); submit(); }} noValidate className="space-y-4">
          <FormField id="assignee" label="Maintenance staff" required error={error ?? undefined}>
            <select id="assignee" className={inputCls(!!error)} value={assignee} onChange={(e) => setAssignee(e.target.value)} aria-invalid={!!error}>
              <option value="">Select staff member</option>
              {options.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          </FormField>
          <FormField id="asg-note" label="Note for staff (optional)">
            <textarea id="asg-note" className={inputCls()} rows={2} maxLength={1000} value={note} onChange={(e) => setNote(e.target.value)} />
          </FormField>
          <button type="submit" className={`${btnPrimary} w-full`} disabled={busy}>{reassign ? "Reassign" : "Assign"}</button>
        </form>
      )}
      <ConfirmDialog open={confirming} title="Reassign this ticket?" message={`The ticket will move from ${ticket.assigned_to?.name} to ${chosen?.name}. The previous assignment is kept in the history.`} confirmLabel="Reassign" busy={busy} onConfirm={run} onCancel={() => setConfirming(false)} />
    </section>
  );
}

function AssignmentTrail({ ticket }: { ticket: Ticket }) {
  return (
    <section className={panel} aria-labelledby="trail-h">
      <CardTitle id="trail-h" icon="route">Assignment trail</CardTitle>
      <ol className="space-y-5 text-sm">
        {ticket.assignments.map((a) => (
          <li key={a.id} className="relative border-l-2 border-slate-200 pl-5">
            <span aria-hidden className={`absolute -left-[7px] top-1 h-3 w-3 rounded-full ring-4 ring-white ${a.is_active ? "bg-brand-600" : "bg-slate-300"}`} />
            <p className="font-semibold text-slate-900">{a.assigned_to.name} {a.is_active && <span className="ml-1 rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-semibold text-emerald-800 ring-1 ring-inset ring-emerald-200">(current)</span>}</p>
            <p className="mt-0.5 text-xs text-slate-500">By {a.assigned_by.name} · {formatDateTime(a.assigned_at)}{a.unassigned_at ? ` → ${formatDateTime(a.unassigned_at)}` : ""}</p>
            {a.assignment_note && <p className="mt-1 text-xs text-slate-700">Note: {a.assignment_note}</p>}
          </li>
        ))}
      </ol>
    </section>
  );
}

/* ----------------------------------------------------------------- attachments */
function Attachments({ ticket, onDone }: { ticket: Ticket; onDone: (m: string) => void }) {
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function upload(file: File | undefined, reset: () => void) {
    const problem = validateImage(file);
    if (problem || !file) return setError(problem);
    setBusy(true);
    setError(null);
    const form = new FormData();
    form.append("file", file);
    try {
      await api(`/api/tickets/${ticket.id}/attachments/`, { method: "POST", form });
      reset();
      onDone("Image attached.");
    } catch (e) {
      setError(e instanceof ApiError && e.fields.file ? e.fields.file : errorMessage(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className={panel} aria-labelledby="att-h">
      <CardTitle id="att-h" icon="image">Attachments</CardTitle>
      {ticket.attachments.length === 0 ? (
        <p className="text-sm text-slate-500">No images attached.</p>
      ) : (
        <ul className="flex flex-wrap gap-4">
          {ticket.attachments.map((a) => (
            <li key={a.id} className="text-xs">
              <a href={`${API_BASE}${a.url}`} target="_blank" rel="noreferrer" className="block overflow-hidden rounded-2xl ring-1 ring-slate-900/10 shadow-sm">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={`${API_BASE}${a.url}`} alt={`Attachment: ${a.original_filename}`} className="h-28 w-28 object-cover transition duration-500 hover:scale-110" />
              </a>
              <p className="mt-2 max-w-[7rem] truncate font-medium text-slate-700">{a.original_filename}</p>
              <p className="text-slate-500">{formatFileSize(a.file_size)}</p>
            </li>
          ))}
        </ul>
      )}
      {ticket.permissions.can_attach && (
        <div className="mt-6 border-t border-slate-100 pt-6">
          <FormField id="att-file" label="Add an image (JPEG, PNG, WEBP or GIF, max 5 MB)" error={error ?? undefined}>
            <input id="att-file" type="file" accept="image/jpeg,image/png,image/webp,image/gif" disabled={busy} className={fileCls}
              onChange={(e) => { const input = e.currentTarget; void upload(input.files?.[0], () => { input.value = ""; }); }} />
          </FormField>
        </div>
      )}
    </section>
  );
}

/* -------------------------------------------------------------------- comments */
function Comments({ ticket, onDone }: { ticket: Ticket; onDone: (m: string) => void }) {
  const [message, setMessage] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit() {
    if (!message.trim()) return setError("Write a comment first.");
    setBusy(true);
    setError(null);
    try {
      await api(`/api/tickets/${ticket.id}/comments/`, { method: "POST", json: { message } });
      setMessage("");
      onDone("Comment added.");
    } catch (e) {
      setError(e instanceof ApiError && e.fields.message ? e.fields.message : errorMessage(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className={panel} aria-labelledby="com-h">
      <CardTitle id="com-h" icon="message">Comments</CardTitle>
      {ticket.comments.length === 0 ? (
        <p className="text-sm text-slate-500">No comments yet.</p>
      ) : (
        <ul className="space-y-4">
          {ticket.comments.map((c) => (
            <li key={c.id} className="flex gap-3 text-sm">
              <span aria-hidden className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-gradient-to-br from-brand-400 to-indigo-600 text-xs font-semibold text-white ring-2 ring-white shadow-sm">{c.author.name.charAt(0).toUpperCase()}</span>
              <div className="min-w-0 flex-1 rounded-2xl rounded-tl-md bg-slate-50 p-3.5 ring-1 ring-inset ring-slate-100">
                <p className="text-xs text-slate-500"><span className="font-semibold text-slate-800">{c.author.name}</span> · {formatDateTime(c.created_at)}</p>
                <p className="mt-1.5 whitespace-pre-wrap break-words leading-relaxed text-slate-800">{c.message}</p>
              </div>
            </li>
          ))}
        </ul>
      )}
      {ticket.permissions.can_comment && (
        <form className="mt-6 space-y-3 border-t border-slate-100 pt-6" noValidate onSubmit={(e) => { e.preventDefault(); void submit(); }}>
          <FormField id="comment" label="Add a comment" error={error ?? undefined}>
            <textarea id="comment" className={inputCls(!!error)} rows={3} maxLength={2000} value={message} onChange={(e) => setMessage(e.target.value)} aria-invalid={!!error} />
          </FormField>
          <button type="submit" className={btnPrimary} disabled={busy}>{busy ? "Posting..." : "Post comment"}</button>
        </form>
      )}
    </section>
  );
}

/* --------------------------------------------------------------------- history */
function History({ ticket }: { ticket: Ticket }) {
  return (
    <section className={panel} aria-labelledby="his-h">
      <CardTitle id="his-h" icon="activity">Activity history</CardTitle>
      {ticket.history.length === 0 ? (
        <EmptyState title="No activity yet" />
      ) : (
        <ol className="space-y-5">
          {ticket.history.map((h) => (
            <li key={h.id} className="relative border-l-2 border-brand-100 pl-5 text-sm">
              <span aria-hidden className="absolute -left-[7px] top-1 h-3 w-3 rounded-full bg-brand-600 ring-4 ring-white" />
              <p className="font-semibold text-slate-900">{describe(h)}</p>
              <p className="mt-0.5 text-xs text-slate-500">{h.changed_by.name} · {formatDateTime(h.created_at)}</p>
              {h.note && <p className="mt-1.5 whitespace-pre-wrap rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-700">“{h.note}”</p>}
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}

function describe(h: Ticket["history"][number]): string {
  const pretty = (v: string | null) => (v && v in STATUS_LABELS ? STATUS_LABELS[v as Status] : v);
  switch (h.event_type) {
    case "CREATED": return "Ticket created";
    case "STATUS": return `Status: ${pretty(h.old_value)} → ${pretty(h.new_value)}`;
    case "PRIORITY": return `Priority: ${h.old_value} → ${h.new_value}`;
    case "ASSIGNMENT": return h.old_value ? `Reassigned: ${h.old_value} → ${h.new_value ?? "nobody"}` : h.new_value ? `Assigned to ${h.new_value}` : "Assignment removed";
    case "DEADLINE": return "Deadlines recalculated";
    case "ATTACHMENT": return `Attachment added: ${h.new_value}`;
    default: return h.event_label;
  }
}
"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import { useAuth } from "@/lib/auth";
import { formatDateTime, STATUS_LABELS } from "@/lib/format";
import { useApiData } from "@/lib/useApi";
import type { CategoryCount, DashboardSummary, Paginated, Priority, Status, TicketSummary } from "@/types";
import { OverdueBadge, PriorityBadge, StatusBadge } from "./Badges";
import { EmptyState, ErrorBanner, PageHeader, Spinner, StatCard } from "./Feedback";
import { Icon } from "./Icons";
import { btnGhost, btnLight, btnSecondary, card, cardHover } from "./ui";

function Hero({ eyebrow, title, subtitle, actions }: { eyebrow: string; title: string; subtitle?: string; actions?: ReactNode }) {
  return (
    <section className="relative mb-7 overflow-hidden rounded-3xl bg-[#0a0f1e] px-6 py-8 text-white shadow-[0_28px_50px_-28px_rgba(10,15,30,0.7)] sm:mb-9 sm:px-10 sm:py-11">
      <div aria-hidden className="pointer-events-none absolute -right-16 -top-24 h-80 w-80 rounded-full bg-brand-500/40 blur-3xl" />
      <div aria-hidden className="pointer-events-none absolute -bottom-32 left-1/4 h-72 w-72 rounded-full bg-indigo-500/25 blur-3xl" />
      <div aria-hidden className="pointer-events-none absolute inset-0 opacity-60 [background-image:radial-gradient(rgba(255,255,255,0.09)_1px,transparent_1px)] [background-size:22px_22px] [mask-image:linear-gradient(to_right,transparent,black_70%)]" />
      <div className="relative flex flex-wrap items-end justify-between gap-6">
        <div className="min-w-0">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-brand-300">{eyebrow}</p>
          <h1 className="mt-2 text-2xl font-semibold tracking-tight sm:text-4xl">{title}</h1>
          {subtitle && <p className="mt-2.5 max-w-xl text-sm leading-relaxed text-slate-300 sm:text-base">{subtitle}</p>}
        </div>
        {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
      </div>
    </section>
  );
}

function RecentList({ title, tickets, basePath, empty }: { title: string; tickets: TicketSummary[]; basePath: string; empty: string }) {
  return (
    <section className={`overflow-hidden ${card}`} aria-label={title}>
      <h2 className="flex items-center gap-2.5 border-b border-slate-100 px-5 py-4 text-[15px] font-semibold text-slate-900 sm:px-6">
        <span aria-hidden className="grid h-7 w-7 place-items-center rounded-lg bg-brand-50 text-brand-600"><Icon name="activity" className="h-4 w-4" /></span>
        {title}
      </h2>
      {tickets.length === 0 ? (
        <p className="px-5 py-8 text-center text-sm text-slate-500 sm:px-6">{empty}</p>
      ) : (
        <ul className="divide-y divide-slate-100">
          {tickets.map((t) => (
            <li key={t.id} className="group flex flex-wrap items-center justify-between gap-3 px-5 py-4 text-sm transition-colors hover:bg-brand-50/40 sm:px-6">
              <div className="min-w-0">
                <Link href={`${basePath}/${t.id}`} className="font-semibold text-slate-900 transition group-hover:text-brand-700">{t.title}</Link>
                <p className="mt-1 font-mono text-xs text-slate-500">{t.ticket_number} · {formatDateTime(t.created_at)}</p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <StatusBadge status={t.status} />
                {t.is_overdue && <OverdueBadge />}
                <span aria-hidden className="hidden text-slate-300 transition group-hover:translate-x-0.5 group-hover:text-brand-500 sm:inline"><Icon name="arrow-right" className="h-4 w-4" /></span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function useSummary() {
  return useApiData<DashboardSummary>("/api/dashboard/summary/");
}

export function StudentDashboard() {
  const { user } = useAuth();
  const { data, error, loading, reload } = useSummary();
  return (
    <div>
      <Hero eyebrow="Student portal" title={`Welcome, ${user?.first_name || user?.name}`} subtitle="Track the issues you have reported." actions={<Link href="/student/tickets/new" className={btnLight}><Icon name="plus" className="h-4 w-4" />Report a new issue</Link>} />
      {loading && !data && <Spinner />}
      {error && <ErrorBanner message={error.message} onRetry={reload} />}
      {data && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-3 sm:gap-5 lg:grid-cols-4">
            <StatCard label="Total reported" value={data.total} icon="layers" />
            <StatCard label="Open / waiting" value={data.open_count ?? 0} icon="inbox" />
            <StatCard label="In progress" value={data.in_progress ?? 0} icon="bolt" />
            <StatCard label="Resolved / closed" value={data.resolved_or_closed ?? 0} icon="check" />
          </div>
          {data.total === 0 ? (
            <EmptyState title="You have not reported any issues yet" hint="Spotted something broken on campus? Report it and track its progress here." action={<Link href="/student/tickets/new" className="btn-primary">Report an issue</Link>} />
          ) : (
            <RecentList title="Recent tickets" tickets={data.recent ?? []} basePath="/student/tickets" empty="No recent tickets." />
          )}
        </div>
      )}
    </div>
  );
}

export function StaffDashboard() {
  const { user } = useAuth();
  const { data, error, loading, reload } = useSummary();
  return (
    <div>
      <Hero eyebrow="Maintenance" title={`Hello, ${user?.first_name || user?.name}`} subtitle="Your assigned work and upcoming deadlines." actions={<Link href="/staff/tickets" className={btnGhost}>All assigned tickets<Icon name="arrow-right" className="h-4 w-4" /></Link>} />
      {loading && !data && <Spinner />}
      {error && <ErrorBanner message={error.message} onRetry={reload} />}
      {data && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-3 sm:gap-5 lg:grid-cols-4">
            <StatCard label="Assigned to me" value={data.assigned ?? 0} hint="Waiting to be started" icon="inbox" />
            <StatCard label="In progress" value={data.in_progress ?? 0} icon="bolt" />
            <StatCard label={`Due within ${data.due_soon_hours ?? 4}h`} value={data.due_soon ?? 0} icon="clock" />
            <StatCard label="Overdue" value={data.overdue ?? 0} tone="danger" icon="alert" />
          </div>
          <RecentList title="Active work" tickets={data.recent ?? []} basePath="/staff/tickets" empty="No active tickets are assigned to you." />
          <RecentList title="Recently completed" tickets={data.recently_completed ?? []} basePath="/staff/tickets" empty="Nothing completed yet." />
        </div>
      )}
    </div>
  );
}

export function ManagerDashboard() {
  const { user } = useAuth();
  const { data, error, loading, reload } = useSummary();
  const isAdmin = user?.role === "ADMINISTRATOR";
  return (
    <div>
      <Hero eyebrow={isAdmin ? "Administration" : "Department"} title={isAdmin ? "Administrator overview" : "Department dashboard"} subtitle={data?.department?.name ?? (isAdmin ? "All departments. Use Django Admin to manage users, departments and categories." : undefined)} actions={<Link href="/manager/tickets" className={btnLight}>Open ticket queue<Icon name="arrow-right" className="h-4 w-4" /></Link>} />
      {loading && !data && <Spinner />}
      {error && <ErrorBanner message={error.message} onRetry={reload} />}
      {data && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-3 sm:gap-5 lg:grid-cols-4">
            <StatCard label="Total tickets" value={data.total} icon="layers" />
            <StatCard label="Unassigned" value={data.unassigned ?? 0} hint="Waiting for a manager" icon="inbox" />
            <StatCard label="Overdue" value={data.overdue ?? 0} tone="danger" icon="alert" />
            <StatCard label="Avg. resolution" value={data.avg_resolution_hours != null ? `${data.avg_resolution_hours} h` : "n/a"} hint={`From ${data.resolved_sample_size ?? 0} resolved ticket(s)`} icon="clock" />
          </div>
          <div className="flex flex-wrap gap-2">
            <Link href="/manager/tickets?unassigned=true" className={btnSecondary}><Icon name="inbox" className="h-4 w-4 text-slate-400" />Review unassigned</Link>
            <Link href="/manager/overdue" className={btnSecondary}><Icon name="clock" className="h-4 w-4 text-slate-400" />View overdue</Link>
            <Link href="/manager/reports" className={btnSecondary}><Icon name="chart" className="h-4 w-4 text-slate-400" />Reports</Link>
          </div>
          {data.total === 0 ? (
            <EmptyState title="No tickets yet" hint="New tickets from students appear here as soon as they are reported." />
          ) : (
            <>
              <div className="grid gap-6 lg:grid-cols-2">
                <Breakdown title="Tickets by status" data={data.by_status} labels={(k) => STATUS_LABELS[k as Status]} />
                <Breakdown title="Tickets by priority" data={data.by_priority} labels={(k) => k.charAt(0) + k.slice(1).toLowerCase()} />
              </div>
              <RecentList title="Latest tickets" tickets={data.recent ?? []} basePath="/manager/tickets" empty="No tickets." />
            </>
          )}
          {isAdmin && data.by_department && (
            <section className={`overflow-hidden ${card}`}>
              <h2 className="flex items-center gap-2.5 border-b border-slate-100 px-5 py-4 text-[15px] font-semibold text-slate-900 sm:px-6">
                <span aria-hidden className="grid h-7 w-7 place-items-center rounded-lg bg-brand-50 text-brand-600"><Icon name="layers" className="h-4 w-4" /></span>
                By department
              </h2>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-slate-50/80 text-left text-[11px] uppercase tracking-wider text-slate-500"><tr><th scope="col" className="px-5 py-3 font-semibold sm:px-6">Department</th><th scope="col" className="px-3 py-3 font-semibold">Total</th><th scope="col" className="px-3 py-3 font-semibold">Active</th></tr></thead>
                  <tbody>{data.by_department.map((d) => <tr key={d.id} className="border-t border-slate-100 transition-colors hover:bg-brand-50/40"><td className="px-5 py-3.5 font-medium text-slate-900 sm:px-6">{d.name}</td><td className="px-3 tabular-nums text-slate-700">{d.tickets_total}</td><td className="px-3 tabular-nums text-slate-700">{d.tickets_open}</td></tr>)}</tbody>
                </table>
              </div>
            </section>
          )}
        </div>
      )}
    </div>
  );
}

function BarRow({ label, value, max, labelWidth }: { label: string; value: number; max: number; labelWidth: string }) {
  return (
    <li className={`grid ${labelWidth} items-center gap-3 text-sm`}>
      <span className="truncate font-medium text-slate-700">{label}</span>
      <span className="h-2.5 overflow-hidden rounded-full bg-slate-100" aria-hidden>
        <span className="block h-full rounded-full bg-gradient-to-r from-brand-300 via-brand-500 to-brand-600 transition-all duration-700" style={{ width: `${(value / max) * 100}%` }} />
      </span>
      <span className="text-right font-semibold tabular-nums text-slate-900">{value}</span>
    </li>
  );
}

function Breakdown({ title, data, labels }: { title: string; data?: Partial<Record<Status | Priority, number>>; labels: (k: string) => string }) {
  if (!data) return null;
  const entries = Object.entries(data) as [string, number][];
  const max = Math.max(1, ...entries.map(([, n]) => n));
  return (
    <section className={`p-5 sm:p-6 ${card}`} aria-label={title}>
      <h2 className="mb-5 flex items-center gap-2.5 text-[15px] font-semibold text-slate-900">
        <span aria-hidden className="grid h-7 w-7 place-items-center rounded-lg bg-brand-50 text-brand-600"><Icon name="chart" className="h-4 w-4" /></span>
        {title}
      </h2>
      <ul className="space-y-3.5">
        {entries.map(([key, n]) => (
          <BarRow key={key} label={labels(key)} value={n} max={max} labelWidth="grid-cols-[6.5rem_1fr_2rem] sm:grid-cols-[7.5rem_1fr_2rem]" />
        ))}
      </ul>
    </section>
  );
}

export function OverdueView({ basePath }: { basePath: string }) {
  const { data, error, loading, reload } = useApiData<{ count: number; results: TicketSummary[] }>("/api/dashboard/overdue/");
  return (
    <div>
      <PageHeader title="Overdue tickets" subtitle="Active tickets whose response or resolution deadline has passed." />
      {loading && !data && <Spinner />}
      {error && <ErrorBanner message={error.message} onRetry={reload} />}
      {data && data.count === 0 && <EmptyState title="Nothing is overdue" hint="All active tickets are within their deadlines." />}
      {data && data.count > 0 && (
        <ul className="space-y-3">
          {data.results.map((t) => (
            <li key={t.id} className={`relative flex flex-wrap items-center justify-between gap-3 overflow-hidden p-4 pl-6 sm:p-5 sm:pl-7 ${card} ${cardHover}`}>
              <span aria-hidden className="absolute inset-y-0 left-0 w-1.5 bg-gradient-to-b from-red-400 to-red-600" />
              <div className="min-w-0">
                <Link href={`${basePath}/${t.id}`} className="font-semibold text-slate-900 transition hover:text-brand-700">{t.title}</Link>
                <p className="mt-1 font-mono text-xs text-slate-500">{t.ticket_number} · {t.assigned_to ? `Assigned to ${t.assigned_to.name}` : "Unassigned"}</p>
                <p className="mt-0.5 text-xs text-slate-600">Resolution due {formatDateTime(t.resolution_due_at)}</p>
              </div>
              <div className="flex flex-wrap gap-2"><StatusBadge status={t.status} /><PriorityBadge priority={t.priority} label={t.priority_label} /><OverdueBadge /></div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function ReportsView() {
  const summary = useSummary();
  const cats = useApiData<CategoryCount[]>("/api/dashboard/categories/");
  const total = Math.max(1, ...(cats.data ?? []).map((c) => c.count));
  return (
    <div>
      <PageHeader title="Reports" subtitle="Summaries calculated from the database within your scope." />
      {(summary.loading || cats.loading) && !summary.data && <Spinner />}
      {(summary.error || cats.error) && <ErrorBanner message={(summary.error ?? cats.error)!.message} onRetry={() => { summary.reload(); cats.reload(); }} />}
      {summary.data && cats.data && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-3 sm:gap-5 lg:grid-cols-4">
            <StatCard label="Total tickets" value={summary.data.total} icon="layers" />
            <StatCard label="Overdue" value={summary.data.overdue ?? 0} tone="danger" icon="alert" />
            <StatCard label="Unassigned" value={summary.data.unassigned ?? 0} icon="inbox" />
            <StatCard label="Avg. resolution" value={summary.data.avg_resolution_hours != null ? `${summary.data.avg_resolution_hours} h` : "n/a"} hint={`${summary.data.resolved_sample_size ?? 0} resolved`} icon="clock" />
          </div>
          <section className={`p-5 sm:p-6 ${card}`}>
            <h2 className="mb-5 flex items-center gap-2.5 text-[15px] font-semibold text-slate-900">
              <span aria-hidden className="grid h-7 w-7 place-items-center rounded-lg bg-brand-50 text-brand-600"><Icon name="chart" className="h-4 w-4" /></span>
              Tickets by category
            </h2>
            {cats.data.length === 0 ? <p className="text-sm text-slate-500">No tickets to report on yet.</p> : (
              <ul className="space-y-3.5">
                {cats.data.map((c) => (
                  <BarRow key={c.category_id} label={c.category} value={c.count} max={total} labelWidth="grid-cols-[7.5rem_1fr_2rem] sm:grid-cols-[10rem_1fr_2rem]" />
                ))}
              </ul>
            )}
          </section>
          <div className="grid gap-6 lg:grid-cols-2">
            <Breakdown title="By status" data={summary.data.by_status} labels={(k) => STATUS_LABELS[k as Status]} />
            <Breakdown title="By priority" data={summary.data.by_priority} labels={(k) => k.charAt(0) + k.slice(1).toLowerCase()} />
          </div>
        </div>
      )}
    </div>
  );
}

export type { Paginated };
"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { formatDateTime } from "@/lib/format";
import { useApiData } from "@/lib/useApi";
import type { Category, Paginated, Priority, Status, TicketSummary } from "@/types";
import { OverdueBadge, PriorityBadge, StatusBadge } from "./Badges";
import { EmptyState, ErrorBanner, Spinner } from "./Feedback";
import { Icon } from "./Icons";
import { Pagination } from "./Pagination";
import { btnSecondary, card, cardHover, inputCls, labelCls } from "./ui";

const PAGE_SIZE = 10;
const STATUSES: Status[] = ["OPEN", "ASSIGNED", "IN_PROGRESS", "RESOLVED", "REOPENED", "CLOSED"];
const PRIORITIES: Priority[] = ["LOW", "MEDIUM", "HIGH", "URGENT"];

export interface TicketFilters {
  search: string;
  status: string;
  priority: string;
  category: string;
  building: string;
  ordering: string;
  unassigned: boolean;
  overdue: boolean;
}

const DEFAULTS: TicketFilters = { search: "", status: "", priority: "", category: "", building: "", ordering: "-created_at", unassigned: false, overdue: false };

interface Props {
  basePath: string; // e.g. "/student/tickets"
  initial?: Partial<TicketFilters>;
  showReporter?: boolean;
  showAssignee?: boolean;
  emptyTitle?: string;
  emptyHint?: string;
}

const checkCls = "h-4 w-4 cursor-pointer rounded border-slate-300 text-brand-600 focus:ring-brand-500";

export function TicketList({ basePath, initial, showReporter, showAssignee = true, emptyTitle = "No tickets found", emptyHint }: Props) {
  const [filters, setFilters] = useState<TicketFilters>({ ...DEFAULTS, ...initial });
  const [search, setSearch] = useState(filters.search);
  const [page, setPage] = useState(1);
  const categories = useApiData<Category[]>("/api/categories/");

  // Debounce the search box so we do not query on every keystroke.
  useEffect(() => {
    const id = setTimeout(() => {
      setFilters((f) => (f.search === search ? f : { ...f, search: search.trim() }));
      setPage(1);
    }, 350);
    return () => clearTimeout(id);
  }, [search]);

  const { data, error, loading, reload } = useApiData<Paginated<TicketSummary>>("/api/tickets/", {
    ...filters,
    page,
    page_size: PAGE_SIZE,
  });

  const update = (patch: Partial<TicketFilters>) => {
    setFilters((f) => ({ ...f, ...patch }));
    setPage(1);
  };
  const clear = () => {
    setSearch("");
    setFilters(DEFAULTS);
    setPage(1);
  };
  const hasFilters = JSON.stringify({ ...filters, ordering: "" }) !== JSON.stringify({ ...DEFAULTS, ordering: "" });

  return (
    <div>
      <form role="search" aria-label="Filter tickets" className={`mb-6 grid gap-4 p-5 sm:grid-cols-2 sm:p-6 lg:grid-cols-4 ${card}`} onSubmit={(e) => e.preventDefault()}>
        <div className="sm:col-span-2">
          <label htmlFor="f-search" className={labelCls}>Search (ticket number, title, description)</label>
          <div className="relative">
            <span aria-hidden className="pointer-events-none absolute inset-y-0 left-3.5 grid place-items-center text-slate-400"><Icon name="search" className="h-4 w-4" /></span>
            <input id="f-search" className={`${inputCls()} pl-10`} value={search} onChange={(e) => setSearch(e.target.value)} placeholder="e.g. CF-2026-000001 or projector" />
          </div>
        </div>
        <div>
          <label htmlFor="f-status" className={labelCls}>Status</label>
          <select id="f-status" className={inputCls()} value={filters.status} onChange={(e) => update({ status: e.target.value })}>
            <option value="">All statuses</option>
            {STATUSES.map((s) => <option key={s} value={s}>{s.replace("_", " ").toLowerCase().replace(/^./, (c) => c.toUpperCase())}</option>)}
          </select>
        </div>
        <div>
          <label htmlFor="f-priority" className={labelCls}>Priority</label>
          <select id="f-priority" className={inputCls()} value={filters.priority} onChange={(e) => update({ priority: e.target.value })}>
            <option value="">All priorities</option>
            {PRIORITIES.map((p) => <option key={p} value={p}>{p.charAt(0) + p.slice(1).toLowerCase()}</option>)}
          </select>
        </div>
        <div>
          <label htmlFor="f-category" className={labelCls}>Category</label>
          <select id="f-category" className={inputCls()} value={filters.category} onChange={(e) => update({ category: e.target.value })}>
            <option value="">All categories</option>
            {categories.data?.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>
        <div>
          <label htmlFor="f-building" className={labelCls}>Building / location</label>
          <input id="f-building" className={inputCls()} value={filters.building} onChange={(e) => update({ building: e.target.value })} placeholder="e.g. Block-A" />
        </div>
        <div>
          <label htmlFor="f-order" className={labelCls}>Sort by</label>
          <select id="f-order" className={inputCls()} value={filters.ordering} onChange={(e) => update({ ordering: e.target.value })}>
            <option value="-created_at">Newest first</option>
            <option value="created_at">Oldest first</option>
            <option value="-updated_at">Recently updated</option>
            <option value="-priority">Priority (highest first)</option>
            <option value="due_date">Due date (soonest first)</option>
          </select>
        </div>
        {showAssignee && (
          <fieldset className="flex flex-wrap items-end gap-x-5 gap-y-2 pb-2.5 text-sm font-medium text-slate-700">
            <legend className="sr-only">Quick filters</legend>
            <label className="flex cursor-pointer items-center gap-2"><input type="checkbox" className={checkCls} checked={filters.unassigned} onChange={(e) => update({ unassigned: e.target.checked })} /> Unassigned only</label>
            <label className="flex cursor-pointer items-center gap-2"><input type="checkbox" className={checkCls} checked={filters.overdue} onChange={(e) => update({ overdue: e.target.checked })} /> Overdue only</label>
          </fieldset>
        )}
        <div className="flex items-end">
          {hasFilters && <button type="button" className={btnSecondary} onClick={clear}><Icon name="close" className="h-4 w-4" />Clear filters</button>}
        </div>
      </form>

      {loading && !data && <Spinner label="Loading tickets..." />}
      {error && <ErrorBanner message={error.message} onRetry={reload} />}

      {data && data.results.length === 0 && (
        <EmptyState title={hasFilters ? "No tickets match your filters" : emptyTitle} hint={hasFilters ? "Try removing a filter or searching for something else." : emptyHint} />
      )}

      {data && data.results.length > 0 && (
        <div className={loading ? "opacity-60 transition" : "transition"} aria-busy={loading}>
          {/* Desktop table */}
          <div className={`hidden overflow-hidden md:block ${card}`}>
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm">
                <caption className="sr-only">Tickets</caption>
                <thead className="border-b border-slate-100 bg-slate-50/80 text-[11px] uppercase tracking-wider text-slate-500">
                  <tr>
                    <th scope="col" className="px-5 py-3.5 font-semibold">Ticket</th>
                    <th scope="col" className="px-4 py-3.5 font-semibold">Title</th>
                    <th scope="col" className="px-4 py-3.5 font-semibold">Status</th>
                    <th scope="col" className="px-4 py-3.5 font-semibold">Priority</th>
                    <th scope="col" className="px-4 py-3.5 font-semibold">Location</th>
                    {showReporter && <th scope="col" className="px-4 py-3.5 font-semibold">Reported by</th>}
                    {showAssignee && <th scope="col" className="px-4 py-3.5 font-semibold">Assigned to</th>}
                    <th scope="col" className="px-4 py-3.5 font-semibold">Due</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {data.results.map((t) => (
                    <tr key={t.id} className="transition-colors hover:bg-brand-50/40">
                      <td className="whitespace-nowrap px-5 py-4 font-mono text-xs"><Link className="rounded-md bg-brand-50 px-2 py-1 font-semibold text-brand-700 ring-1 ring-inset ring-brand-100 transition hover:bg-brand-100" href={`${basePath}/${t.id}`}>{t.ticket_number}</Link></td>
                      <td className="max-w-xs px-4 py-4 font-semibold text-slate-900">{t.title}<div className="mt-0.5 text-xs font-normal text-slate-500">{t.category.name}</div></td>
                      <td className="px-4 py-4"><StatusBadge status={t.status} /></td>
                      <td className="px-4 py-4"><PriorityBadge priority={t.priority} label={t.priority_label} /></td>
                      <td className="px-4 py-4 text-slate-700">{t.building}{t.room_or_area ? `, ${t.room_or_area}` : ""}</td>
                      {showReporter && <td className="px-4 py-4 text-slate-700">{t.reporter.name}</td>}
                      {showAssignee && <td className="px-4 py-4 text-slate-700">{t.assigned_to?.name ?? <span className="text-slate-400">Unassigned</span>}</td>}
                      <td className="whitespace-nowrap px-4 py-4 text-xs text-slate-600">{formatDateTime(t.resolution_due_at)} {t.is_overdue && <OverdueBadge />}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          {/* Mobile cards */}
          <ul className="space-y-3 md:hidden">
            {data.results.map((t) => (
              <li key={t.id} className={`p-4 ${card} ${cardHover} active:scale-[0.99]`}>
                <Link href={`${basePath}/${t.id}`} className="block">
                  <div className="flex items-start justify-between gap-3">
                    <p className="font-mono text-xs font-semibold text-brand-700">{t.ticket_number}</p>
                    <Icon name="arrow-right" className="h-4 w-4 shrink-0 text-slate-300" />
                  </div>
                  <p className="mt-1.5 font-semibold text-slate-900">{t.title}</p>
                  <div className="mt-3 flex flex-wrap gap-2"><StatusBadge status={t.status} /><PriorityBadge priority={t.priority} label={t.priority_label} />{t.is_overdue && <OverdueBadge />}</div>
                  <p className="mt-3 flex items-center gap-1.5 text-xs text-slate-500"><Icon name="pin" className="h-3.5 w-3.5" />{t.building} · {t.category.name}</p>
                  {showAssignee && <p className="mt-1 flex items-center gap-1.5 text-xs text-slate-500"><Icon name="user" className="h-3.5 w-3.5" />Assigned to: {t.assigned_to?.name ?? "Unassigned"}</p>}
                </Link>
              </li>
            ))}
          </ul>
          <Pagination page={page} count={data.count} pageSize={PAGE_SIZE} onPage={setPage} />
        </div>
      )}
    </div>
  );
}
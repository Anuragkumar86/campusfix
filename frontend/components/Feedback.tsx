import type { ReactNode } from "react";
import { Icon, type IconName } from "./Icons";
import { btnSecondary, card, cardHover } from "./ui";

export function Spinner({ label = "Loading..." }: { label?: string }) {
  return (
    <div role="status" aria-live="polite" className="flex flex-col items-center justify-center gap-3 py-14 text-slate-500">
      <span className="relative h-9 w-9" aria-hidden>
        <span className="absolute inset-0 rounded-full border-2 border-brand-100" />
        <span className="absolute inset-0 animate-spin rounded-full border-2 border-transparent border-t-brand-600" />
      </span>
      <span className="text-sm font-medium">{label}</span>
    </div>
  );
}

export function ErrorBanner({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div role="alert" className="flex animate-fade-in flex-wrap items-center justify-between gap-3 rounded-2xl bg-red-50 px-4 py-3.5 text-sm text-red-900 ring-1 ring-inset ring-red-200">
      <span className="flex items-center gap-3">
        <span aria-hidden className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-red-100 text-red-600">
          <Icon name="alert" className="h-4 w-4" />
        </span>
        {message}
      </span>
      {onRetry && (
        <button type="button" className={`${btnSecondary} !py-1.5`} onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  );
}

export function SuccessBanner({ children }: { children: ReactNode }) {
  return (
    <div role="status" className="flex animate-fade-in items-center gap-3 rounded-2xl bg-emerald-50 px-4 py-3.5 text-sm text-emerald-900 ring-1 ring-inset ring-emerald-200">
      <span aria-hidden className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-emerald-100 text-emerald-600">
        <Icon name="check" className="h-4 w-4" />
      </span>
      <span>{children}</span>
    </div>
  );
}

export function EmptyState({ title, hint, action }: { title: string; hint?: string; action?: ReactNode }) {
  return (
    <div className="relative overflow-hidden rounded-3xl border border-dashed border-slate-300 bg-white/70 px-6 py-14 text-center">
      <div aria-hidden className="pointer-events-none absolute left-1/2 top-6 h-32 w-32 -translate-x-1/2 rounded-full bg-brand-200/50 blur-3xl" />
      <div aria-hidden className="relative mx-auto mb-5 grid h-16 w-16 place-items-center rounded-full bg-brand-50 ring-8 ring-brand-50/60">
        <span className="grid h-11 w-11 place-items-center rounded-full bg-white text-brand-600 shadow-sm ring-1 ring-brand-100">
          <Icon name="inbox" className="h-5 w-5" />
        </span>
      </div>
      <p className="relative text-base font-semibold text-slate-900">{title}</p>
      {hint && <p className="relative mx-auto mt-1.5 max-w-sm text-sm leading-relaxed text-slate-500">{hint}</p>}
      {action && <div className="relative mt-6">{action}</div>}
    </div>
  );
}

export function PageHeader({ title, subtitle, actions }: { title: string; subtitle?: string; actions?: ReactNode }) {
  return (
    <div className="mb-7 flex flex-wrap items-end justify-between gap-4 sm:mb-9">
      <div className="min-w-0">
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900 sm:text-[1.75rem]">{title}</h1>
        <span aria-hidden className="mt-3 block h-1 w-10 rounded-full bg-gradient-to-r from-brand-500 to-brand-300" />
        {subtitle && <p className="mt-3 max-w-2xl text-sm leading-relaxed text-slate-500 sm:text-[15px]">{subtitle}</p>}
      </div>
      {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
    </div>
  );
}

export function StatCard({ label, value, hint, tone = "default", icon }: { label: string; value: number | string; hint?: string; tone?: "default" | "danger"; icon?: IconName }) {
  const danger = tone === "danger" && Number(value) > 0;
  return (
    <div className={`group relative overflow-hidden p-4 sm:p-5 ${card} ${cardHover}`}>
      <div aria-hidden className={`pointer-events-none absolute -right-8 -top-8 h-28 w-28 rounded-full opacity-70 blur-2xl transition-opacity duration-300 group-hover:opacity-100 ${danger ? "bg-red-300/50" : "bg-brand-200/70"}`} />
      <div className="relative flex items-start justify-between gap-3">
        <p className="text-[13px] font-medium text-slate-500">{label}</p>
        {icon && (
          <span className={`grid h-9 w-9 shrink-0 place-items-center rounded-xl ring-1 ring-inset ${danger ? "bg-red-50 text-red-600 ring-red-100" : "bg-brand-50 text-brand-600 ring-brand-100"}`}>
            <Icon name={icon} className="h-[18px] w-[18px]" />
          </span>
        )}
      </div>
      <p className={`relative mt-3 text-3xl font-semibold tabular-nums tracking-tight ${danger ? "text-red-700" : "text-slate-900"}`}>{value}</p>
      {hint && <p className="relative mt-1 text-xs text-slate-500">{hint}</p>}
    </div>
  );
}
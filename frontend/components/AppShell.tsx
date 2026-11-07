"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState, type ReactNode } from "react";
import { API_BASE } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Icon, type IconName } from "./Icons";

export interface NavItem { href: string; label: string; external?: boolean }

function iconFor(item: NavItem): IconName {
  if (item.external) return "shield";
  const h = item.href;
  if (h.includes("unassigned")) return "inbox";
  if (h.endsWith("/new")) return "plus";
  if (h.includes("overdue")) return "clock";
  if (h.includes("reports")) return "chart";
  if (h.endsWith("/tickets")) return "list";
  return "home";
}

function BrandMark() {
  return (
    <span className="flex items-center gap-3">
      <span aria-hidden className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-brand-300 via-brand-500 to-brand-700 text-base font-bold text-white shadow-[0_8px_20px_-6px_rgba(91,111,232,0.8)] ring-1 ring-white/20">
        C
      </span>
      <span className="text-[17px] font-semibold tracking-tight text-white">CampusFix</span>
    </span>
  );
}

export function AppShell({ nav, children }: { nav: NavItem[]; children: ReactNode }) {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const [open, setOpen] = useState(false);

  const isActive = (href: string) => {
    const path = href.split("?")[0];
    if (href.includes("?")) return false;
    const roots = ["/student", "/staff", "/manager"];
    return roots.includes(path) ? pathname === path : pathname === path || pathname.startsWith(`${path}/`);
  };

  async function onLogout() {
    await logout();
    router.replace("/login");
  }

  return (
    <div className="min-h-screen md:flex">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-50 focus:rounded-lg focus:bg-white focus:px-3 focus:py-2 focus:shadow-lg">
        Skip to main content
      </a>

      <header className="sticky top-0 z-40 flex items-center justify-between border-b border-white/10 bg-[#0a0f1e]/95 px-4 py-3 text-white backdrop-blur md:hidden">
        <BrandMark />
        <button type="button" className="inline-flex items-center gap-2 rounded-xl bg-white/10 px-3 py-1.5 text-sm font-medium ring-1 ring-inset ring-white/15 transition hover:bg-white/20" aria-expanded={open} aria-controls="side-nav" onClick={() => setOpen((v) => !v)}>
          <Icon name={open ? "close" : "menu"} className="h-4 w-4" />
          {open ? "Close menu" : "Menu"}
        </button>
      </header>

      <aside id="side-nav" className={`${open ? "flex animate-slide-down" : "hidden"} relative flex-col overflow-hidden bg-[#0a0f1e] text-white md:fixed md:inset-y-0 md:flex md:w-72 md:animate-none md:border-r md:border-white/5`}>
        <div aria-hidden className="pointer-events-none absolute -left-24 -top-28 h-80 w-80 rounded-full bg-brand-500/30 blur-3xl" />
        <div aria-hidden className="pointer-events-none absolute -bottom-28 -right-24 h-72 w-72 rounded-full bg-indigo-500/20 blur-3xl" />

        <div className="relative hidden px-6 pb-3 pt-7 md:block"><BrandMark /></div>
        <p className="relative px-6 pb-2 pt-4 text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Menu</p>

        <nav aria-label="Main" className="relative flex flex-1 flex-col gap-1 overflow-y-auto px-3 pb-3">
          {nav.map((item) => {
            if (item.external) {
              return (
                <a key={item.href} href={item.href} target="_blank" rel="noreferrer" className="group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-slate-400 transition hover:bg-white/5 hover:text-white">
                  <Icon name={iconFor(item)} className="h-[18px] w-[18px] text-slate-500 transition group-hover:text-brand-300" />
                  <span className="flex-1">{item.label}</span>
                  <span aria-hidden><Icon name="external" className="h-3.5 w-3.5 opacity-60" /></span>
                </a>
              );
            }
            const active = isActive(item.href);
            return (
              <Link key={item.href} href={item.href} onClick={() => setOpen(false)} aria-current={active ? "page" : undefined}
                className={`group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${active ? "bg-white/10 text-white ring-1 ring-inset ring-white/10" : "text-slate-400 hover:bg-white/5 hover:text-white"}`}>
                {active && <span aria-hidden className="absolute -left-3 top-1/2 h-5 w-1 -translate-y-1/2 rounded-r-full bg-gradient-to-b from-brand-300 to-brand-500" />}
                <Icon name={iconFor(item)} className={`h-[18px] w-[18px] transition ${active ? "text-brand-300" : "text-slate-500 group-hover:text-brand-300"}`} />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="relative m-3 rounded-2xl bg-white/5 p-3.5 ring-1 ring-inset ring-white/10 backdrop-blur">
          <div className="flex items-center gap-3">
            <span aria-hidden className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-gradient-to-br from-brand-400 to-indigo-600 text-sm font-semibold text-white ring-2 ring-white/20">
              {user?.name?.charAt(0).toUpperCase()}
            </span>
            <div className="min-w-0 text-sm">
              <p className="truncate font-semibold text-white">{user?.name}</p>
              <p className="truncate text-xs text-slate-400">{user?.role_label}</p>
              {user?.department && <p className="truncate text-xs text-slate-500">{user.department.name}</p>}
            </div>
          </div>
          <button type="button" onClick={onLogout} className="mt-3 flex w-full items-center gap-2 rounded-xl bg-white/5 px-3 py-2 text-sm font-medium text-slate-300 ring-1 ring-inset ring-white/10 transition hover:bg-white/10 hover:text-white">
            <Icon name="logout" className="h-4 w-4" />
            Sign out
          </button>
        </div>
      </aside>

      <main id="main" className="min-w-0 flex-1 px-4 py-6 sm:px-6 md:ml-72 md:px-10 md:py-10">
        <div className="mx-auto max-w-6xl animate-fade-up">{children}</div>
      </main>
    </div>
  );
}

export const adminLink: NavItem = { href: `${API_BASE}/admin/`, label: "Django Admin", external: true };
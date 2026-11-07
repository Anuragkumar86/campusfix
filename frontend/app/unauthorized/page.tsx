"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { roleHome } from "@/lib/format";

export default function Unauthorized() {
  const { user } = useAuth();
  return (
    <main className="relative flex min-h-screen flex-col items-center justify-center gap-4 overflow-hidden px-4 text-center">
      <div aria-hidden className="pointer-events-none absolute -left-24 -top-24 h-96 w-96 rounded-full bg-amber-100/60 blur-3xl" />
      <div aria-hidden className="pointer-events-none absolute -bottom-32 -right-24 h-96 w-96 rounded-full bg-brand-200/40 blur-3xl" />
      <div className="relative flex animate-fade-up flex-col items-center gap-3">
        <span aria-hidden className="grid h-14 w-14 place-items-center rounded-2xl bg-amber-50 text-amber-600 ring-1 ring-amber-200">
          <svg viewBox="0 0 24 24" className="h-7 w-7 fill-none stroke-current" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <rect x="5" y="11" width="14" height="9" rx="2" />
            <path d="M8 11V8a4 4 0 118 0v3" />
          </svg>
        </span>
        <h1 className="text-2xl font-semibold text-slate-900 sm:text-3xl">Access denied</h1>
        <p className="max-w-md text-slate-600">Your account does not have permission to view that page.</p>
        <Link href={user ? roleHome(user.role) : "/login"} className="btn-primary mt-2">{user ? "Back to my dashboard" : "Sign in"}</Link>
      </div>
    </main>
  );
}
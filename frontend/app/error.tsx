"use client";

export default function GlobalError({ reset }: { error: Error; reset: () => void }) {
  return (
    <main className="relative flex min-h-screen flex-col items-center justify-center gap-4 overflow-hidden px-4 text-center" role="alert">
      <div aria-hidden className="pointer-events-none absolute -left-24 -top-24 h-96 w-96 rounded-full bg-red-100/60 blur-3xl" />
      <div aria-hidden className="pointer-events-none absolute -bottom-32 -right-24 h-96 w-96 rounded-full bg-brand-200/40 blur-3xl" />
      <div className="relative flex animate-fade-up flex-col items-center gap-3">
        <span aria-hidden className="grid h-14 w-14 place-items-center rounded-2xl bg-red-50 text-red-600 ring-1 ring-red-200">
          <svg viewBox="0 0 24 24" className="h-7 w-7 fill-none stroke-current" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 9v4m0 4h.01M10.3 3.9L2.4 17.5A2 2 0 004.1 20.5h15.8a2 2 0 001.7-3L13.7 3.9a2 2 0 00-3.4 0z" />
          </svg>
        </span>
        <h1 className="text-2xl font-semibold text-slate-900 sm:text-3xl">Something went wrong</h1>
        <p className="max-w-sm text-slate-600">An unexpected error occurred in the page. Your data is safe.</p>
        <button type="button" className="btn-primary mt-2" onClick={reset}>Try again</button>
      </div>
    </main>
  );
}
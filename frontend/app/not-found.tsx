import Link from "next/link";

export default function NotFound() {
  return (
    <main className="relative flex min-h-screen flex-col items-center justify-center gap-4 overflow-hidden px-4 text-center">
      <div aria-hidden className="pointer-events-none absolute -left-24 -top-24 h-96 w-96 rounded-full bg-brand-200/50 blur-3xl" />
      <div aria-hidden className="pointer-events-none absolute -bottom-32 -right-24 h-96 w-96 rounded-full bg-indigo-200/40 blur-3xl" />
      <div className="relative flex animate-fade-up flex-col items-center gap-3">
        <p aria-hidden className="bg-gradient-to-br from-brand-400 to-brand-700 bg-clip-text text-7xl font-bold tracking-tight text-transparent sm:text-8xl">404</p>
        <h1 className="text-2xl font-semibold text-slate-900 sm:text-3xl">Page not found</h1>
        <p className="max-w-sm text-slate-600">The page you are looking for does not exist.</p>
        <Link href="/" className="btn-primary mt-2">Go to home</Link>
      </div>
    </main>
  );
}
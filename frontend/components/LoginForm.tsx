"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";
import { errorMessage } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { roleHome } from "@/lib/format";
import { validateLogin, type FormErrors } from "@/lib/validators";
import { ErrorBanner, Spinner } from "./Feedback";
import { FormField } from "./FormField";
import { Icon, type IconName } from "./Icons";
import { btnPrimary, inputCls } from "./ui";

const POINTS: { icon: IconName; title: string; text: string }[] = [
  { icon: "plus", title: "Report in seconds", text: "Describe the problem, pick a location and attach a photo." },
  { icon: "route", title: "Track every step", text: "See who is assigned and what has changed, all in one timeline." },
  { icon: "check", title: "Get it resolved", text: "Deadlines and priorities keep every issue moving." },
];

export function LoginForm() {
  const { user, loading, login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<FormErrors<"email" | "password">>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!loading && user) router.replace(roleHome(user.role));
  }, [loading, user, router]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setFormError(null);
    const found = validateLogin(email, password);
    setErrors(found);
    if (Object.keys(found).length) return;
    setBusy(true);
    try {
      const u = await login(email, password);
      router.replace(roleHome(u.role));
    } catch (err) {
      setFormError(errorMessage(err));
      setBusy(false);
    }
  }

  if (loading || user) return <Spinner label="Loading..." />;

  return (
    <div className="grid min-h-screen lg:grid-cols-[1.05fr_1fr]">
      {/* Brand panel */}
      <aside className="relative hidden overflow-hidden bg-[#0a0f1e] p-12 text-white lg:flex lg:flex-col lg:justify-between">
        <div aria-hidden className="pointer-events-none absolute -left-24 -top-24 h-[28rem] w-[28rem] rounded-full bg-brand-500/30 blur-3xl" />
        <div aria-hidden className="pointer-events-none absolute -bottom-32 -right-20 h-[26rem] w-[26rem] rounded-full bg-indigo-500/25 blur-3xl" />
        <div aria-hidden className="pointer-events-none absolute inset-0 opacity-60 [background-image:radial-gradient(rgba(255,255,255,0.09)_1px,transparent_1px)] [background-size:24px_24px] [mask-image:linear-gradient(to_bottom,black,transparent_85%)]" />

        <div className="relative flex items-center gap-3">
          <span aria-hidden className="grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br from-brand-300 via-brand-500 to-brand-700 font-bold shadow-[0_8px_20px_-6px_rgba(91,111,232,0.8)] ring-1 ring-white/20">C</span>
          <span className="text-lg font-semibold tracking-tight">CampusFix</span>
        </div>

        <div className="relative max-w-md">
          <h2 className="text-4xl font-semibold leading-[1.15] tracking-tight">
            Fix campus issues,
            <span className="block bg-gradient-to-r from-brand-200 to-brand-400 bg-clip-text text-transparent">faster than ever.</span>
          </h2>
          <ul className="mt-10 space-y-6">
            {POINTS.map((p) => (
              <li key={p.title} className="flex gap-4">
                <span aria-hidden className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-white/10 text-brand-200 ring-1 ring-inset ring-white/15">
                  <Icon name={p.icon} className="h-5 w-5" />
                </span>
                <div>
                  <p className="font-semibold">{p.title}</p>
                  <p className="mt-0.5 text-sm leading-relaxed text-slate-400">{p.text}</p>
                </div>
              </li>
            ))}
          </ul>
        </div>

        <p className="relative text-xs text-slate-500">Campus issue reporting and resolution</p>
      </aside>

      {/* Form panel */}
      <div className="relative flex items-center justify-center overflow-hidden px-4 py-12 sm:px-8">
        <div aria-hidden className="pointer-events-none absolute -right-24 -top-24 h-80 w-80 rounded-full bg-brand-200/40 blur-3xl lg:hidden" />
        <div className="relative w-full max-w-sm animate-fade-up">
          <div className="mb-8 lg:hidden">
            <span aria-hidden className="mb-4 grid h-12 w-12 place-items-center rounded-2xl bg-gradient-to-br from-brand-300 via-brand-500 to-brand-700 text-xl font-bold text-white shadow-[0_10px_24px_-8px_rgba(91,111,232,0.8)]">C</span>
            <h1 className="text-3xl font-semibold tracking-tight text-slate-900">CampusFix</h1>
            <p className="mt-1 text-sm text-slate-500">Campus issue reporting and resolution</p>
          </div>

          <form onSubmit={onSubmit} noValidate className="space-y-5">
            <div>
              <h2 className="text-2xl font-semibold tracking-tight text-slate-900 lg:text-3xl">Welcome back</h2>
              <p className="mt-1.5 text-sm text-slate-500">Sign in to continue to your dashboard.</p>
            </div>
            {formError && <ErrorBanner message={formError} />}
            <FormField id="email" label="Email" required error={errors.email}>
              <input id="email" type="email" autoComplete="username" className={inputCls(!!errors.email)} value={email} onChange={(e) => setEmail(e.target.value)} aria-invalid={!!errors.email} />
            </FormField>
            <FormField id="password" label="Password" required error={errors.password}>
              <input id="password" type="password" autoComplete="current-password" className={inputCls(!!errors.password)} value={password} onChange={(e) => setPassword(e.target.value)} aria-invalid={!!errors.password} />
            </FormField>
            <button type="submit" className={`${btnPrimary} w-full !py-3`} disabled={busy}>
              {busy ? "Signing in..." : "Sign in"}
              {!busy && <Icon name="arrow-right" className="h-4 w-4" />}
            </button>
            <p className="text-center text-xs text-slate-500">Accounts are created by an administrator.</p>
          </form>
        </div>
      </div>
    </div>
  );
}
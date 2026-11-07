"use client";

import Link from "next/link";
import { useState, type FormEvent, type ReactNode } from "react";
import { api, ApiError, errorMessage } from "@/lib/api";
import { useApiData } from "@/lib/useApi";
import { validateImage, validateTicketForm, type FormErrors, type TicketFormValues } from "@/lib/validators";
import type { Category, TicketDetail } from "@/types";
import { ErrorBanner, PageHeader, Spinner } from "./Feedback";
import { FormField } from "./FormField";
import { Icon } from "./Icons";
import { btnPrimary, btnSecondary, card, fileCls, inputCls } from "./ui";

// Sample locations only (suggestions). Free text is allowed.
const BUILDINGS = ["Block-A", "Block-B", "Library", "Hostel-1", "Canteen"];
const EMPTY: TicketFormValues = { title: "", description: "", category: "", building: "", floor: "", room_or_area: "" };

function Section({ step, title, hint, children }: { step: number; title: string; hint: string; children: ReactNode }) {
  return (
    <section aria-label={title} className="grid gap-5 border-t border-slate-100 pt-7 first:border-0 first:pt-0 lg:grid-cols-[13rem_1fr] lg:gap-10">
      <div>
        <span aria-hidden className="grid h-7 w-7 place-items-center rounded-lg bg-brand-600 text-xs font-bold text-white shadow-[0_6px_14px_-6px_rgba(59,64,192,0.8)]">{step}</span>
        <h2 className="mt-3 text-base font-semibold text-slate-900">{title}</h2>
        <p className="mt-1 text-sm leading-relaxed text-slate-500">{hint}</p>
      </div>
      <div className="space-y-5">{children}</div>
    </section>
  );
}

export function NewTicketForm() {
  const categories = useApiData<Category[]>("/api/categories/");
  const [values, setValues] = useState<TicketFormValues>(EMPTY);
  const [image, setImage] = useState<File | null>(null);
  const [errors, setErrors] = useState<FormErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [created, setCreated] = useState<{ id: number; ticket_number: string } | null>(null);
  const [fileKey, setFileKey] = useState(0);

  const set = (k: keyof TicketFormValues) => (e: { target: { value: string } }) => setValues((v) => ({ ...v, [k]: e.target.value }));

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setFormError(null);
    const found = validateTicketForm(values);
    const imageProblem = validateImage(image);
    if (imageProblem) found.image = imageProblem;
    setErrors(found);
    if (Object.keys(found).length) return;

    const form = new FormData();
    Object.entries(values).forEach(([k, v]) => form.append(k, v.trim()));
    if (image) form.append("image", image);

    setBusy(true);
    try {
      const ticket = await api<TicketDetail>("/api/tickets/", { method: "POST", form });
      setCreated({ id: ticket.id, ticket_number: ticket.ticket_number });
      setValues(EMPTY);
      setImage(null);
      setFileKey((k) => k + 1);
    } catch (err) {
      if (err instanceof ApiError && Object.keys(err.fields).length) setErrors(err.fields);
      setFormError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  if (created) {
    return (
      <div className={`relative mx-auto max-w-lg animate-scale-in overflow-hidden px-6 py-12 text-center sm:px-10 ${card}`} role="status">
        <div aria-hidden className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-emerald-400 to-brand-500" />
        <div aria-hidden className="pointer-events-none absolute left-1/2 top-0 h-40 w-40 -translate-x-1/2 rounded-full bg-emerald-200/50 blur-3xl" />
        <span aria-hidden className="relative mx-auto grid h-16 w-16 place-items-center rounded-full bg-emerald-50 ring-8 ring-emerald-50/70">
          <span className="grid h-11 w-11 place-items-center rounded-full bg-emerald-500 text-white shadow-[0_10px_24px_-8px_rgba(16,185,129,0.8)]">
            <Icon name="check" className="h-6 w-6" />
          </span>
        </span>
        <h1 className="relative mt-6 text-2xl font-semibold tracking-tight text-slate-900">Issue reported</h1>
        <p className="relative mt-2 text-sm text-slate-500">Your ticket number is</p>
        <p className="relative my-4 inline-block rounded-xl bg-slate-900 px-5 py-2.5 font-mono text-2xl font-semibold tracking-wide text-white shadow-lg shadow-slate-900/20">{created.ticket_number}</p>
        <p className="relative text-sm text-slate-500">Keep this reference to track your issue.</p>
        <div className="relative mt-8 flex flex-wrap justify-center gap-3">
          <Link href={`/student/tickets/${created.id}`} className={btnPrimary}>View ticket</Link>
          <button type="button" className={btnSecondary} onClick={() => setCreated(null)}>Report another issue</button>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl">
      <PageHeader title="Report an issue" subtitle="Tell us what is wrong and where. A maintenance team will be assigned." />
      {categories.loading && <Spinner label="Loading categories..." />}
      {categories.error && <ErrorBanner message={categories.error.message} onRetry={categories.reload} />}
      {categories.data && (
        <form onSubmit={onSubmit} noValidate className={`space-y-8 p-5 sm:p-8 ${card}`}>
          {formError && <ErrorBanner message={formError} />}

          <Section step={1} title="What is wrong?" hint="A short title and a clear description help us route it quickly.">
            <FormField id="title" label="Title" required error={errors.title}>
              <input id="title" className={inputCls(!!errors.title)} value={values.title} onChange={set("title")} maxLength={200} aria-invalid={!!errors.title} />
            </FormField>
            <FormField id="description" label="Description" required error={errors.description}>
              <textarea id="description" rows={5} className={`${inputCls(!!errors.description)} resize-y`} value={values.description} onChange={set("description")} maxLength={5000} aria-invalid={!!errors.description} />
            </FormField>
            <FormField id="category" label="Category" required error={errors.category}>
              <select id="category" className={inputCls(!!errors.category)} value={values.category} onChange={set("category")} aria-invalid={!!errors.category}>
                <option value="">Select a category</option>
                {categories.data.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </FormField>
          </Section>

          <Section step={2} title="Where is it?" hint="Pick a building or type your own. Floor and room are optional.">
            <div className="grid gap-4 sm:grid-cols-3">
              <FormField id="building" label="Building / block" required error={errors.building}>
                <input id="building" list="buildings" className={inputCls(!!errors.building)} value={values.building} onChange={set("building")} maxLength={100} aria-invalid={!!errors.building} />
                <datalist id="buildings">{BUILDINGS.map((b) => <option key={b} value={b} />)}</datalist>
              </FormField>
              <FormField id="floor" label="Floor (optional)" error={errors.floor}>
                <input id="floor" className={inputCls()} value={values.floor} onChange={set("floor")} maxLength={20} />
              </FormField>
              <FormField id="room_or_area" label="Room / area (optional)" error={errors.room_or_area}>
                <input id="room_or_area" className={inputCls()} value={values.room_or_area} onChange={set("room_or_area")} maxLength={100} />
              </FormField>
            </div>
          </Section>

          <Section step={3} title="Add a photo" hint="A picture often saves a site visit.">
            <FormField id="image" label="Photo (optional)" hint="JPEG, PNG, WEBP or GIF, up to 5 MB." error={errors.image}>
              <input key={fileKey} id="image" type="file" accept="image/jpeg,image/png,image/webp,image/gif" className={fileCls} onChange={(e) => setImage(e.target.files?.[0] ?? null)} />
            </FormField>
          </Section>

          <div className="flex flex-col-reverse gap-3 border-t border-slate-100 pt-6 sm:flex-row sm:justify-end">
            <Link href="/student/tickets" className={btnSecondary}>Cancel</Link>
            <button type="submit" className={btnPrimary} disabled={busy}>{busy ? "Submitting..." : "Submit issue"}</button>
          </div>
        </form>
      )}
    </div>
  );
}
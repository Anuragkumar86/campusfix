import type { ReactNode } from "react";

interface Props {
  id: string;
  label: string;
  error?: string;
  hint?: string;
  required?: boolean;
  children: ReactNode;
}

/** Label + control + inline error. The control must use the same `id`. */
export function FormField({ id, label, error, hint, required, children }: Props) {
  return (
    <div>
      <label htmlFor={id} className="mb-1.5 block text-sm font-medium text-slate-800">
        {label} {required && <span aria-hidden className="text-brand-600">*</span>}
        {required && <span className="sr-only">(required)</span>}
      </label>
      {children}
      {hint && !error && <p id={`${id}-hint`} className="mt-1.5 text-xs text-slate-500">{hint}</p>}
      {error && <p id={`${id}-error`} role="alert" className="mt-1.5 animate-fade-in text-sm font-medium text-red-700">{error}</p>}
    </div>
  );
}
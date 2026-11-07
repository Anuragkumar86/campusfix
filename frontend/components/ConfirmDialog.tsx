"use client";

import { useEffect, useRef } from "react";
import { btnDanger, btnPrimary, btnSecondary } from "./ui";
import { Icon } from "./Icons";

interface Props {
  open: boolean;
  title: string;
  message: string;
  confirmLabel: string;
  danger?: boolean;
  busy?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({ open, title, message, confirmLabel, danger, busy, onConfirm, onCancel }: Props) {
  const cancelRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;
    cancelRef.current?.focus();
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onCancel();
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onCancel]);

  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex animate-fade-in items-end justify-center bg-slate-950/60 p-4 backdrop-blur-sm sm:items-center" role="presentation">
      <div role="alertdialog" aria-modal="true" aria-labelledby="confirm-title" aria-describedby="confirm-message" className="relative w-full max-w-md animate-scale-in overflow-hidden rounded-3xl bg-white p-6 shadow-pop ring-1 ring-slate-900/10 sm:p-7">
        <div aria-hidden className={`absolute inset-x-0 top-0 h-1 ${danger ? "bg-gradient-to-r from-red-400 to-red-600" : "bg-gradient-to-r from-brand-400 to-brand-600"}`} />
        <span aria-hidden className={`grid h-11 w-11 place-items-center rounded-2xl ring-1 ring-inset ${danger ? "bg-red-50 text-red-600 ring-red-100" : "bg-brand-50 text-brand-600 ring-brand-100"}`}>
          <Icon name={danger ? "alert" : "shield"} className="h-5 w-5" />
        </span>
        <h2 id="confirm-title" className="mt-4 text-lg font-semibold tracking-tight text-slate-900">{title}</h2>
        <p id="confirm-message" className="mt-1.5 text-sm leading-relaxed text-slate-600">{message}</p>
        <div className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <button ref={cancelRef} type="button" className={btnSecondary} onClick={onCancel} disabled={busy}>
            Cancel
          </button>
          <button type="button" className={danger ? btnDanger : btnPrimary} onClick={onConfirm} disabled={busy}>
            {busy ? "Working..." : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
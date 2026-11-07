export const card =
  "rounded-2xl bg-white ring-1 ring-slate-900/[0.06] shadow-[0_1px_2px_rgba(15,23,42,0.04),0_14px_32px_-18px_rgba(15,23,42,0.18)]";

export const cardHover =
  "transition duration-200 hover:-translate-y-0.5 hover:shadow-[0_1px_2px_rgba(15,23,42,0.05),0_22px_40px_-20px_rgba(15,23,42,0.28)]";

const btn =
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-xl px-4 py-2.5 text-sm font-semibold transition duration-200 active:scale-[0.98] disabled:pointer-events-none disabled:opacity-50";

export const btnPrimary = `${btn} bg-gradient-to-b from-brand-500 to-brand-700 text-white shadow-[inset_0_1px_0_rgba(255,255,255,0.22),0_8px_18px_-8px_rgba(59,64,192,0.75)] hover:from-brand-600 hover:to-brand-800`;
export const btnSecondary = `${btn} bg-white text-slate-700 shadow-sm ring-1 ring-inset ring-slate-200 hover:bg-slate-50 hover:ring-slate-300`;
export const btnDanger = `${btn} bg-gradient-to-b from-red-500 to-red-600 text-white shadow-[inset_0_1px_0_rgba(255,255,255,0.2),0_8px_18px_-8px_rgba(220,38,38,0.7)] hover:from-red-600 hover:to-red-700`;
export const btnLight = `${btn} bg-white text-slate-900 shadow-lg shadow-black/10 hover:bg-brand-50`;
export const btnGhost = `${btn} bg-white/10 text-white ring-1 ring-inset ring-white/20 backdrop-blur hover:bg-white/20`;

const inputBase =
  "block w-full rounded-xl border-0 bg-white px-3.5 py-2.5 text-sm text-slate-900 shadow-sm ring-1 ring-inset transition placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-offset-0";

export const inputCls = (error?: boolean) =>
  `${inputBase} ${error ? "ring-red-300 focus:ring-red-500" : "ring-slate-200 hover:ring-slate-300 focus:ring-brand-500"}`;

export const labelCls = "mb-1.5 block text-xs font-semibold uppercase tracking-wide text-slate-500";

export const fileCls =
  "block w-full cursor-pointer rounded-xl border border-dashed border-slate-300 bg-slate-50/70 p-2.5 text-sm text-slate-600 transition hover:border-brand-400 hover:bg-brand-50/40 file:mr-3 file:cursor-pointer file:rounded-lg file:border-0 file:bg-brand-600 file:px-3.5 file:py-1.5 file:text-sm file:font-semibold file:text-white hover:file:bg-brand-700";
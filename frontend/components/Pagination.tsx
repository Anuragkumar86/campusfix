interface Props {
  page: number;
  count: number;
  pageSize: number;
  onPage: (page: number) => void;
}

const pill =
  "inline-flex items-center rounded-xl bg-white px-3.5 py-2 text-sm font-semibold text-slate-700 shadow-sm ring-1 ring-inset ring-slate-200 transition hover:bg-slate-50 hover:ring-slate-300 active:scale-[0.98] disabled:pointer-events-none disabled:opacity-40";

export function Pagination({ page, count, pageSize, onPage }: Props) {
  const pages = Math.max(1, Math.ceil(count / pageSize));
  if (count === 0) return null;
  const from = (page - 1) * pageSize + 1;
  const to = Math.min(page * pageSize, count);
  return (
    <nav aria-label="Pagination" className="mt-6 flex flex-wrap items-center justify-between gap-3 text-sm text-slate-500">
      <p>
        Showing <span className="font-semibold text-slate-900">{from}-{to}</span> of <span className="font-semibold text-slate-900">{count}</span>
      </p>
      <div className="flex items-center gap-2">
        <button type="button" className={pill} disabled={page <= 1} onClick={() => onPage(page - 1)}>
          Previous
        </button>
        <span aria-current="page" className="rounded-xl bg-brand-50 px-3 py-2 text-sm font-semibold tabular-nums text-brand-700 ring-1 ring-inset ring-brand-100">
          Page {page} of {pages}
        </span>
        <button type="button" className={pill} disabled={page >= pages} onClick={() => onPage(page + 1)}>
          Next
        </button>
      </div>
    </nav>
  );
}
/**
 * Shared API client. Session cookie is HttpOnly (never visible to JS); every
 * request sends it with credentials: "include". Unsafe methods add the CSRF
 * token in the X-CSRFToken header.
 */
export const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000").replace(/\/$/, "");

export const UNAUTHORIZED_EVENT = "campusfix:unauthorized";

export class ApiError extends Error {
  status: number;
  fields: Record<string, string>;
  constructor(status: number, message: string, fields: Record<string, string> = {}) {
    super(message);
    this.status = status;
    this.fields = fields;
  }
  /** "network" | "unauthenticated" | "forbidden" | "not_found" | "conflict" | "validation" | "server" */
  get kind() {
    if (this.status === 0) return "network";
    if (this.status === 401) return "unauthenticated";
    if (this.status === 403) return "forbidden";
    if (this.status === 404) return "not_found";
    if (this.status === 409) return "conflict";
    if (this.status === 400) return "validation";
    return "server";
  }
}

type QueryValue = string | number | boolean | null | undefined;

export function buildQuery(query?: Record<string, QueryValue>): string {
  if (!query) return "";
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value === undefined || value === null || value === "" || value === false) continue;
    params.set(key, String(value));
  }
  const text = params.toString();
  return text ? `?${text}` : "";
}

/** Turn a DRF error body into one message plus per-field messages. */
export function parseErrors(data: unknown, status: number): { message: string; fields: Record<string, string> } {
  const fallback: Record<number, string> = {
    401: "Your session has expired. Please sign in again.",
    403: "You do not have permission to do that.",
    404: "We could not find what you were looking for.",
    409: "That action conflicts with the current state of the ticket.",
    500: "Something went wrong on the server. Please try again.",
  };
  if (data && typeof data === "object" && !Array.isArray(data)) {
    const record = data as Record<string, unknown>;
    if (typeof record.detail === "string") return { message: record.detail, fields: {} };
    const fields: Record<string, string> = {};
    let general = "";
    for (const [key, value] of Object.entries(record)) {
      const text = Array.isArray(value) ? value.map(String).join(" ") : String(value);
      if (key === "non_field_errors") general = text;
      else fields[key] = text;
    }
    if (Object.keys(fields).length || general) {
      return { message: general || "Please correct the highlighted fields.", fields };
    }
  }
  return { message: fallback[status] ?? "Unexpected error. Please try again.", fields: {} };
}

let csrfToken: string | null = null;

export function resetCsrf() {
  csrfToken = null;
}

async function getCsrfToken(): Promise<string> {
  if (csrfToken) return csrfToken;
  const res = await fetch(`${API_BASE}/api/auth/csrf/`, { credentials: "include" });
  if (!res.ok) throw new ApiError(res.status, "Could not start a secure session.");
  csrfToken = ((await res.json()) as { csrfToken: string }).csrfToken;
  return csrfToken;
}

export interface RequestOptions {
  method?: "GET" | "POST" | "PATCH";
  json?: unknown;
  form?: FormData;
  query?: Record<string, QueryValue>;
  signal?: AbortSignal;
}

async function send(path: string, opts: RequestOptions, unsafe: boolean): Promise<Response> {
  const headers: Record<string, string> = {};
  let body: BodyInit | undefined;
  if (opts.json !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(opts.json);
  } else if (opts.form) {
    body = opts.form; // browser sets the multipart boundary
  }
  if (unsafe) headers["X-CSRFToken"] = await getCsrfToken();
  try {
    return await fetch(`${API_BASE}${path}${buildQuery(opts.query)}`, {
      method: opts.method ?? "GET",
      credentials: "include",
      headers,
      body,
      signal: opts.signal,
    });
  } catch (error) {
    if ((error as Error).name === "AbortError") throw error;
    throw new ApiError(0, "Cannot reach the server. Check your connection and that the backend is running.");
  }
}

export async function api<T = unknown>(path: string, opts: RequestOptions = {}): Promise<T> {
  const unsafe = (opts.method ?? "GET") !== "GET";
  let res = await send(path, opts, unsafe);

  if (res.status === 403 && unsafe) {
    // A rejected CSRF check changes nothing on the server, so one retry with a fresh token is safe.
    const isJson = res.headers.get("content-type")?.includes("application/json");
    const text = await res.clone().text();
    if (!isJson || /csrf/i.test(text)) {
      resetCsrf();
      res = await send(path, opts, unsafe);
    }
  }

  if (res.status === 204) return undefined as T;
  let data: unknown = null;
  try {
    data = await res.json();
  } catch {
    /* non-JSON body */
  }
  if (!res.ok) {
    const { message, fields } = parseErrors(data, res.status);
    if (res.status === 401 && typeof window !== "undefined" && !path.startsWith("/api/auth/")) {
      window.dispatchEvent(new Event(UNAUTHORIZED_EVENT));
    }
    throw new ApiError(res.status, message, fields);
  }
  return data as T;
}

export const errorMessage = (error: unknown): string =>
  error instanceof ApiError ? error.message : "Unexpected error. Please try again.";

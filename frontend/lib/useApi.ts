"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api, ApiError, type RequestOptions } from "@/lib/api";

interface State<T> { data: T | null; error: ApiError | null; loading: boolean }

/** GET helper with loading / error state, cancellation and manual reload. */
export function useApiData<T>(path: string | null, query?: RequestOptions["query"]) {
  const [state, setState] = useState<State<T>>({ data: null, error: null, loading: path !== null });
  const key = `${path}|${JSON.stringify(query ?? {})}`;
  const queryRef = useRef(query);
  queryRef.current = query;
  const [tick, setTick] = useState(0);

  useEffect(() => {
    if (path === null) return;
    const controller = new AbortController();
    setState((s) => ({ ...s, loading: true, error: null }));
    api<T>(path, { query: queryRef.current, signal: controller.signal })
      .then((data) => setState({ data, error: null, loading: false }))
      .catch((error) => {
        if ((error as Error).name === "AbortError") return;
        setState({ data: null, error: error instanceof ApiError ? error : new ApiError(500, "Unexpected error."), loading: false });
      });
    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, tick]);

  const reload = useCallback(() => setTick((t) => t + 1), []);
  return { ...state, reload };
}

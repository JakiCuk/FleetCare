import { useCallback, useEffect, useState } from 'react';
import { apiErrorMessage } from '@/api/client';

export interface AsyncResult<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  /** Re-run the fetcher (e.g. after a mutation). */
  reload: () => void;
  setData: (data: T) => void;
}

/**
 * Generic data-fetching hook with loading / error state and manual reload.
 * `deps` controls re-fetching (same semantics as useEffect deps).
 */
export function useApi<T>(
  fetcher: () => Promise<T>,
  deps: ReadonlyArray<unknown> = [],
): AsyncResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  const reload = useCallback(() => setTick((t) => t + 1), []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    fetcher()
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((err) => {
        if (!cancelled) setError(apiErrorMessage(err));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick]);

  return { data, loading, error, reload, setData };
}

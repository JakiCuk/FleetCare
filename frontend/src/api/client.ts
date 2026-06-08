import axios, {
  type AxiosError,
  type AxiosInstance,
  type AxiosRequestConfig,
  type InternalAxiosRequestConfig,
} from 'axios';
import type { RefreshResponse } from '@/types';

const API_BASE = import.meta.env.VITE_API_BASE || '/api';

/**
 * Token accessor wiring. The auth store registers callbacks so the client can
 * read the current access token and persist a refreshed one without importing
 * the store (avoids a circular dependency: store -> client -> store).
 */
let getAccessToken: () => string | null = () => null;
let onTokenRefreshed: (token: string) => void = () => {};
let onAuthFailure: () => void = () => {};

export function configureAuthBridge(bridge: {
  getAccessToken: () => string | null;
  onTokenRefreshed: (token: string) => void;
  onAuthFailure: () => void;
}): void {
  getAccessToken = bridge.getAccessToken;
  onTokenRefreshed = bridge.onTokenRefreshed;
  onAuthFailure = bridge.onAuthFailure;
}

export const api: AxiosInstance = axios.create({
  baseURL: API_BASE,
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
});

// ── Request interceptor: attach Bearer token ────────────────────────────────
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getAccessToken();
  if (token) {
    config.headers.set('Authorization', `Bearer ${token}`);
  }
  return config;
});

// ── Response interceptor: single-flight refresh on 401 + retry queue ────────
interface RetriableRequest extends AxiosRequestConfig {
  _retry?: boolean;
}

let isRefreshing = false;
let refreshWaiters: Array<(token: string | null) => void> = [];

function flushWaiters(token: string | null): void {
  refreshWaiters.forEach((resolve) => resolve(token));
  refreshWaiters = [];
}

/** Bare axios call so the refresh request itself never re-enters the interceptor. */
async function requestRefresh(): Promise<string | null> {
  try {
    const res = await axios.post<RefreshResponse>(
      `${API_BASE}/auth/refresh`,
      {},
      { withCredentials: true },
    );
    return res.data.access_token;
  } catch {
    return null;
  }
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as (RetriableRequest & InternalAxiosRequestConfig) | undefined;
    const status = error.response?.status;
    const url = original?.url ?? '';

    // Do not attempt refresh for auth endpoints or already-retried requests.
    const isAuthCall =
      url.includes('/auth/login') ||
      url.includes('/auth/refresh') ||
      url.includes('/auth/logout');

    if (status !== 401 || !original || original._retry || isAuthCall) {
      return Promise.reject(error);
    }

    original._retry = true;

    if (isRefreshing) {
      // Queue this request until the in-flight refresh resolves.
      return new Promise((resolve, reject) => {
        refreshWaiters.push((token) => {
          if (!token) {
            reject(error);
            return;
          }
          original.headers.set('Authorization', `Bearer ${token}`);
          resolve(api(original));
        });
      });
    }

    isRefreshing = true;
    const newToken = await requestRefresh();
    isRefreshing = false;

    if (!newToken) {
      flushWaiters(null);
      onAuthFailure();
      return Promise.reject(error);
    }

    onTokenRefreshed(newToken);
    flushWaiters(newToken);
    original.headers.set('Authorization', `Bearer ${newToken}`);
    return api(original);
  },
);

/** Normalise API error to a human-readable string (`detail` field or fallback). */
export function apiErrorMessage(err: unknown, fallback = 'error'): string {
  if (axios.isAxiosError(err)) {
    const detail = (err.response?.data as { detail?: unknown } | undefined)?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0] as { msg?: string };
      if (first?.msg) return first.msg;
    }
    if (err.message) return err.message;
  }
  return fallback;
}

export default api;

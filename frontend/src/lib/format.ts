/** Formatting helpers. Locale-aware where it matters; defaults to sk-SK. */

const LOCALE_KEY = 'fleetcare.locale';

function activeLocale(): string {
  if (typeof localStorage !== 'undefined') {
    const stored = localStorage.getItem(LOCALE_KEY);
    if (stored === 'en') return 'en-GB';
  }
  return 'sk-SK';
}

export function formatKm(km: number | null | undefined): string {
  if (km === null || km === undefined) return '—';
  return `${km.toLocaleString(activeLocale())} km`;
}

/** Compact km for chart axes: 127540 -> "127.5k". */
export function formatKmCompact(km: number): string {
  if (Math.abs(km) >= 1000) return `${(km / 1000).toFixed(1)}k`;
  return String(km);
}

export function formatMoney(
  amount: number | null | undefined,
  currency = 'EUR',
): string {
  if (amount === null || amount === undefined) return '—';
  return new Intl.NumberFormat(activeLocale(), {
    style: 'currency',
    currency,
    maximumFractionDigits: 2,
  }).format(amount);
}

/** Price with 4 decimals (e.g. fuel price per liter: "1,6890 €"). */
export function formatPrice(
  amount: number | null | undefined,
  currency = 'EUR',
): string {
  if (amount === null || amount === undefined) return '—';
  return new Intl.NumberFormat(activeLocale(), {
    style: 'currency',
    currency,
    minimumFractionDigits: 4,
    maximumFractionDigits: 4,
  }).format(amount);
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '—';
  return d.toLocaleDateString(activeLocale(), {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
}

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '—';
  return d.toLocaleString(activeLocale(), {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatNumber(
  value: number | null | undefined,
  digits = 1,
): string {
  if (value === null || value === undefined) return '—';
  return value.toLocaleString(activeLocale(), {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

export function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase() ?? '')
    .join('');
}

/** Today's date as an ISO date string (yyyy-mm-dd) for date inputs. */
export function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

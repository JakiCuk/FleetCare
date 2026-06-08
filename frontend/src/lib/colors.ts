import type { ChipVariant, StatusColor } from '@/types';

/**
 * Color rule by remaining days (DESIGN_SYSTEM §1 / TECHNICAL_SPECIFICATION §7.4):
 *   days < 0 or <= 7  -> red
 *   <= 30             -> yellow
 *   else              -> green
 *   null              -> gray
 * `urgentThreshold` lets STK/insurance use the stricter <=14 rule in car detail.
 */
export function chipColors(
  days: number | null | undefined,
  urgentThreshold = 7,
): StatusColor {
  if (days === null || days === undefined) return 'gray';
  if (days < 0 || days <= urgentThreshold) return 'red';
  if (days <= 30) return 'yellow';
  return 'green';
}

/** Tread color (DESIGN_SYSTEM §1): <3 red, <5 orange/yellow, else green. */
export function treadColor(mm: number | null | undefined): StatusColor {
  if (mm === null || mm === undefined) return 'gray';
  if (mm < 3) return 'red';
  if (mm < 5) return 'yellow';
  return 'green';
}

/** Hex tread color for the wheel diagram (orange tier per §5 mockup wording). */
export function treadHex(mm: number | null | undefined): string {
  if (mm === null || mm === undefined) return '#94a3b8';
  if (mm < 3) return '#dc2626';
  if (mm < 5) return '#ea580c';
  return '#16a34a';
}

/**
 * Service interval urgency (TECHNICAL_SPECIFICATION §7.3):
 *   km_left < 500 or days_left <= 14 -> red
 *   km_left < 2000 or days_left <= 30 -> yellow
 *   else green.
 */
export function intervalColor(
  kmLeft: number | null | undefined,
  daysLeft: number | null | undefined,
): StatusColor {
  const km = kmLeft ?? Infinity;
  const days = daysLeft ?? Infinity;
  if (km < 500 || days <= 14) return 'red';
  if (km < 2000 || days <= 30) return 'yellow';
  return 'green';
}

/** Map a status color to the corresponding chip variant. */
export function statusToVariant(status: StatusColor): ChipVariant {
  return status;
}

/** Tailwind classes (text + bg) for each chip/badge variant (DESIGN_SYSTEM §1). */
export const variantClasses: Record<ChipVariant, string> = {
  green: 'text-state-green bg-state-green-bg',
  yellow: 'text-state-yellow bg-state-yellow-bg',
  red: 'text-state-red bg-state-red-bg',
  blue: 'text-state-blue bg-state-blue-bg',
  purple: 'text-state-purple bg-state-purple-bg',
  orange: 'text-state-orange bg-state-orange-bg',
  gray: 'text-state-gray bg-state-gray-bg',
};

/** Left-border (rail) hex per status color for upcoming-date cards. */
export const railHex: Record<StatusColor, string> = {
  red: '#dc2626',
  yellow: '#d97706',
  green: '#16a34a',
  gray: '#94a3b8',
};

/** Cost pie-chart category colors (DESIGN_SYSTEM §6). */
export const expenseCategoryHex: Record<string, string> = {
  fuel: '#3b82f6',
  service: '#f59e0b',
  documents: '#8b5cf6',
  tires: '#10b981',
  other: '#94a3b8',
};

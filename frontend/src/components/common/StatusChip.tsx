import { chipColors, variantClasses } from '@/lib/colors';
import { cn } from '@/lib/cn';

interface StatusChipProps {
  label: string;
  days: number | null;
  /** Stricter red threshold (e.g. 14 for STK/insurance in car detail). */
  urgentThreshold?: number;
  className?: string;
}

/** Pill with `LABEL Xd`, colored by remaining days (DESIGN_SYSTEM §1/§4). */
export function StatusChip({ label, days, urgentThreshold, className }: StatusChipProps) {
  const variant = chipColors(days, urgentThreshold);
  const suffix = days === null ? '—' : `${days}d`;
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded px-2 py-0.5 text-xs font-semibold',
        variantClasses[variant],
        className,
      )}
    >
      <span>{label}</span>
      <span>{suffix}</span>
    </span>
  );
}

export default StatusChip;

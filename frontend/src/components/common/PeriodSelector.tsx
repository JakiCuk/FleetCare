import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { cn } from '@/lib/cn';
import { Input } from './Input';

export type PeriodPreset = 'month' | 'year' | 'custom';

export interface PeriodValue {
  from_date?: string;
  to_date?: string;
  /** Aggregation granularity for stats endpoints. */
  group_by: 'month' | 'year';
}

interface PeriodSelectorProps {
  value: PeriodValue;
  onChange: (value: PeriodValue) => void;
  className?: string;
}

function pad(n: number): string {
  return String(n).padStart(2, '0');
}

/** First/last day of the current month as yyyy-mm-dd. */
function thisMonthRange(): { from_date: string; to_date: string } {
  const now = new Date();
  const y = now.getFullYear();
  const m = now.getMonth();
  const last = new Date(y, m + 1, 0).getDate();
  return { from_date: `${y}-${pad(m + 1)}-01`, to_date: `${y}-${pad(m + 1)}-${pad(last)}` };
}

/** First/last day of the current year as yyyy-mm-dd. */
function thisYearRange(): { from_date: string; to_date: string } {
  const y = new Date().getFullYear();
  return { from_date: `${y}-01-01`, to_date: `${y}-12-31` };
}

/** Compute the default ("this month") preset value. */
export function defaultPeriod(): PeriodValue {
  return { ...thisMonthRange(), group_by: 'month' };
}

/**
 * Period selector: "this month" / "this year" presets plus a custom from/to
 * range. Emits ISO date strings + a `group_by` granularity for stats.
 */
export function PeriodSelector({ value, onChange, className }: PeriodSelectorProps) {
  const { t } = useTranslation();
  const [preset, setPreset] = useState<PeriodPreset>('month');

  function selectPreset(p: PeriodPreset) {
    setPreset(p);
    if (p === 'month') {
      onChange({ ...thisMonthRange(), group_by: 'month' });
    } else if (p === 'year') {
      onChange({ ...thisYearRange(), group_by: 'year' });
    } else {
      // Keep current range; default group_by to month for custom.
      onChange({ from_date: value.from_date, to_date: value.to_date, group_by: value.group_by });
    }
  }

  const presets: { key: PeriodPreset; label: string }[] = [
    { key: 'month', label: t('period.thisMonth') },
    { key: 'year', label: t('period.thisYear') },
    { key: 'custom', label: t('period.custom') },
  ];

  return (
    <div className={cn('flex flex-wrap items-end gap-2', className)}>
      <div className="flex gap-2">
        {presets.map((p) => (
          <button
            key={p.key}
            type="button"
            onClick={() => selectPreset(p.key)}
            className={cn(
              'rounded-full border px-3 py-1.5 text-[13px] font-medium transition',
              preset === p.key
                ? 'border-primary bg-primary-bg text-primary'
                : 'border-border bg-surface text-text-muted hover:bg-bg',
            )}
          >
            {p.label}
          </button>
        ))}
      </div>

      {preset === 'custom' && (
        <div className="flex items-end gap-2">
          <label className="flex flex-col gap-1 text-[11px] text-text-muted">
            {t('period.from')}
            <Input
              type="date"
              value={value.from_date ?? ''}
              onChange={(e) => onChange({ ...value, from_date: e.target.value || undefined })}
              className="w-auto"
            />
          </label>
          <label className="flex flex-col gap-1 text-[11px] text-text-muted">
            {t('period.to')}
            <Input
              type="date"
              value={value.to_date ?? ''}
              onChange={(e) => onChange({ ...value, to_date: e.target.value || undefined })}
              className="w-auto"
            />
          </label>
          <div className="flex gap-1">
            {(['month', 'year'] as const).map((g) => (
              <button
                key={g}
                type="button"
                onClick={() => onChange({ ...value, group_by: g })}
                className={cn(
                  'rounded border px-2.5 py-1.5 text-xs font-medium transition',
                  value.group_by === g
                    ? 'border-primary bg-primary-bg text-primary'
                    : 'border-border bg-surface text-text-muted hover:bg-bg',
                )}
              >
                {g === 'month' ? t('period.byMonth') : t('period.byYear')}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default PeriodSelector;

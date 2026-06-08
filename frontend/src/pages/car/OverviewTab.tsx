import { useMemo, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { carsApi } from '@/api/cars';
import { apiErrorMessage } from '@/api/client';
import { useApi } from '@/hooks/useApi';
import { useUiStore } from '@/stores/uiStore';
import { Btn, Card, ErrorState, Input, LoadingState } from '@/components/common';
import { OdometerChart } from '@/components/charts';
import { chipColors, railHex } from '@/lib/colors';
import { formatKm } from '@/lib/format';
import { cn } from '@/lib/cn';
import type { CarDetail, StatusColor } from '@/types';

interface UpcomingItem {
  key: string;
  category: string;
  title: string;
  meta: string;
  days: number | null;
  km: number | null;
  status: StatusColor;
}

const statusRank: Record<StatusColor, number> = { red: 0, yellow: 1, green: 2, gray: 3 };

function buildUpcoming(car: CarDetail, t: (k: string) => string): UpcomingItem[] {
  const items: UpcomingItem[] = [];
  const docThreshold = 14; // STK/insurance use stricter <=14 red rule.

  if (car.stk) {
    items.push({
      key: 'stk',
      category: 'STK',
      title: 'STK',
      meta: car.stk.provider ?? '—',
      days: car.stk.days_left,
      km: null,
      status: chipColors(car.stk.days_left, docThreshold),
    });
  }
  if (car.pzp) {
    items.push({
      key: 'pzp',
      category: 'PZP',
      title: 'PZP',
      meta: car.pzp.provider ?? '—',
      days: car.pzp.days_left,
      km: null,
      status: chipColors(car.pzp.days_left, docThreshold),
    });
  }
  if (car.kasko) {
    items.push({
      key: 'kasko',
      category: 'KASKO',
      title: 'KASKO',
      meta: car.kasko.provider ?? '—',
      days: car.kasko.days_left,
      km: null,
      status: chipColors(car.kasko.days_left, docThreshold),
    });
  }
  for (const v of car.vignettes) {
    items.push({
      key: `vignette-${v.id}`,
      category: v.country,
      title: `${t('documents.typeVignetteSk').split(' ')[0]} ${v.country}`,
      meta: '—',
      days: v.days_left,
      km: null,
      status: chipColors(v.days_left),
    });
  }
  if (car.next_service) {
    items.push({
      key: 'service',
      category: t('car.tabService'),
      title: car.next_service.name,
      meta: car.next_service.label,
      days: car.next_service.days_left,
      km: car.next_service.km_left,
      status: chipColors(car.next_service.days_left ?? null),
    });
  }

  return items.sort((a, b) => statusRank[a.status] - statusRank[b.status]);
}

export function OverviewTab({ car, onChanged }: { car: CarDetail; onChanged: () => void }) {
  const { t } = useTranslation();
  const pushToast = useUiStore((s) => s.pushToast);

  const odo = useApi(() => carsApi.odometer(car.id), [car.id]);
  const [reading, setReading] = useState(String(car.current_odometer_km));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const upcoming = useMemo(() => buildUpcoming(car, t), [car, t]);
  const counts = useMemo(
    () => ({
      red: upcoming.filter((u) => u.status === 'red').length,
      yellow: upcoming.filter((u) => u.status === 'yellow').length,
      green: upcoming.filter((u) => u.status === 'green' || u.status === 'gray').length,
    }),
    [upcoming],
  );

  async function saveReading(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await carsApi.addOdometer(car.id, { reading_km: Number(reading) });
      pushToast(t('overview.odometerSaved'), 'success');
      odo.reload();
      onChanged();
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  function suffix(item: UpcomingItem): string {
    if (item.days !== null && item.days < 0) {
      return `⚠ ${t('overview.agoDays').replace('{{count}}', String(Math.abs(item.days)))}`;
    }
    if (item.km !== null && item.km !== undefined) {
      return t('overview.inKm').replace('{{count}}', String(item.km));
    }
    if (item.days !== null) {
      return t('overview.inDays').replace('{{count}}', String(item.days));
    }
    return '—';
  }

  return (
    <div className="grid grid-cols-1 gap-5 lg:grid-cols-[1fr_320px]">
      <div className="flex flex-col gap-5">
        <Card title={t('overview.odometerState')}>
          <form onSubmit={saveReading} className="flex items-end gap-3">
            <div className="flex-1">
              <label className="mb-1 block text-[13px] font-medium text-text">
                {t('overview.odometerCurrent')}
              </label>
              <Input
                type="number"
                value={reading}
                onChange={(e) => setReading(e.target.value)}
                className="text-lg"
              />
            </div>
            <Btn type="submit" disabled={saving}>
              {saving ? t('common.saving') : t('overview.odometerSave')}
            </Btn>
          </form>
          {error && <p className="mt-2 text-sm text-state-red">{error}</p>}
        </Card>

        <Card title={t('overview.odometerHistory')}>
          {odo.loading && <LoadingState />}
          {odo.error && <ErrorState message={odo.error} onRetry={odo.reload} />}
          {odo.data && odo.data.length > 0 ? (
            <OdometerChart readings={odo.data} />
          ) : (
            odo.data && <p className="py-6 text-center text-sm text-text-faint">{t('common.noData')}</p>
          )}
        </Card>
      </div>

      <Card title={t('overview.upcoming')}>
        <div className="mb-4 flex gap-2 text-xs">
          <span className="rounded bg-state-red-bg px-2 py-1 font-semibold text-state-red">
            {counts.red} {t('overview.urgent')}
          </span>
          <span className="rounded bg-state-yellow-bg px-2 py-1 font-semibold text-state-yellow">
            {counts.yellow} {t('overview.soon')}
          </span>
          <span className="rounded bg-state-green-bg px-2 py-1 font-semibold text-state-green">
            {counts.green} {t('overview.ok')}
          </span>
        </div>

        {upcoming.length === 0 ? (
          <p className="py-6 text-center text-sm text-text-faint">{t('overview.noUpcoming')}</p>
        ) : (
          <ul className="flex flex-col gap-2">
            {upcoming.map((item) => (
              <li
                key={item.key}
                className="flex items-center justify-between gap-2 rounded-md border border-border-soft bg-bg/40 py-2 pl-3 pr-3"
                style={{ borderLeft: `3px solid ${railHex[item.status]}` }}
              >
                <div className="min-w-0">
                  <div className="text-[11px] uppercase tracking-wide text-text-faint">
                    {item.category}
                  </div>
                  <div className="truncate text-[13px] font-medium text-text">{item.title}</div>
                  <div className="truncate text-xs text-text-muted">{item.meta}</div>
                </div>
                <span
                  className={cn(
                    'shrink-0 rounded px-2 py-0.5 text-xs font-semibold',
                    item.status === 'red' && 'bg-state-red-bg text-state-red',
                    item.status === 'yellow' && 'bg-state-yellow-bg text-state-yellow',
                    (item.status === 'green' || item.status === 'gray') && 'bg-state-green-bg text-state-green',
                  )}
                >
                  {suffix(item)}
                </span>
              </li>
            ))}
          </ul>
        )}
        <div className="mt-3 text-xs text-text-faint">
          {formatKm(car.current_odometer_km)}
        </div>
      </Card>
    </div>
  );
}

export default OverviewTab;

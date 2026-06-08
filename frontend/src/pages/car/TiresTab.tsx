import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { tiresApi } from '@/api/tires';
import { useApi } from '@/hooks/useApi';
import {
  Badge,
  Btn,
  Card,
  Column,
  EmptyState,
  ErrorState,
  LoadingState,
  StatCard,
  Table,
} from '@/components/common';
import { TireTrendChart } from '@/components/charts';
import { formatDate, formatKm, formatNumber } from '@/lib/format';
import { cn } from '@/lib/cn';
import type { TireMeasurement, TireSet, TireTrend } from '@/types';
import { WheelDiagram } from './tires/WheelDiagram';
import { MeasurementModal } from './tires/MeasurementModal';
import { TireSetModal } from './tires/TireSetModal';

function seasonLabel(season: string, t: (k: string) => string): string {
  if (season === 'summer') return t('tires.seasonSummer');
  if (season === 'winter') return t('tires.seasonWinter');
  return t('tires.seasonAllseason');
}

function latestMeasurement(set: TireSet): TireMeasurement | null {
  if (set.measurements.length === 0) return null;
  return [...set.measurements].sort(
    (a, b) => +new Date(b.measured_at) - +new Date(a.measured_at),
  )[0];
}

export function TiresTab({ carId, currentOdometer }: { carId: number; currentOdometer: number }) {
  const { t } = useTranslation();
  const { data, loading, error, reload } = useApi(() => tiresApi.list(carId), [carId]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [measurementOpen, setMeasurementOpen] = useState(false);
  const [setOpen, setSetOpen] = useState(false);

  // Default the selection to the active set once data arrives.
  useEffect(() => {
    if (data && selectedId === null) {
      const active = data.find((s) => s.is_active) ?? data[0];
      if (active) setSelectedId(active.id);
    }
  }, [data, selectedId]);

  const selected = useMemo(
    () => data?.find((s) => s.id === selectedId) ?? null,
    [data, selectedId],
  );

  const [trend, setTrend] = useState<TireTrend | null>(null);
  useEffect(() => {
    let cancelled = false;
    if (selectedId !== null) {
      tiresApi
        .trend(selectedId)
        .then((r) => !cancelled && setTrend(r))
        .catch(() => !cancelled && setTrend(null));
    }
    return () => {
      cancelled = true;
    };
  }, [selectedId]);

  const measurementColumns: Column<TireMeasurement>[] = [
    { key: 'date', header: t('tires.colDate'), render: (m) => formatDate(m.measured_at) },
    { key: 'odo', header: t('tires.colOdometer'), align: 'right', render: (m) => formatKm(m.odometer_km) },
    { key: 'fl', header: 'FL', align: 'right', render: (m) => formatNumber(m.tread_fl_mm) },
    { key: 'fr', header: 'FR', align: 'right', render: (m) => formatNumber(m.tread_fr_mm) },
    { key: 'rl', header: 'RL', align: 'right', render: (m) => formatNumber(m.tread_rl_mm) },
    { key: 'rr', header: 'RR', align: 'right', render: (m) => formatNumber(m.tread_rr_mm) },
    {
      key: 'avg',
      header: t('tires.colAvg'),
      align: 'right',
      render: (m) =>
        formatNumber((m.tread_fl_mm + m.tread_fr_mm + m.tread_rl_mm + m.tread_rr_mm) / 4),
    },
    {
      key: 'pressure',
      header: t('tires.colPressure'),
      align: 'right',
      render: (m) => {
        const vals = [m.pressure_fl_after_bar, m.pressure_fr_after_bar, m.pressure_rl_after_bar, m.pressure_rr_after_bar].filter(
          (v): v is number => typeof v === 'number',
        );
        if (vals.length === 0) return '—';
        return formatNumber(vals.reduce((a, b) => a + b, 0) / vals.length, 1);
      },
    },
  ];

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap gap-2">
          {(data ?? []).map((s) => (
            <button
              key={s.id}
              type="button"
              onClick={() => setSelectedId(s.id)}
              className={cn(
                'rounded-full border px-3 py-1.5 text-[13px] font-medium transition',
                s.id === selectedId
                  ? 'border-primary bg-primary-bg text-primary'
                  : 'border-border bg-surface text-text-muted hover:bg-bg',
              )}
            >
              {s.is_active && <span className="mr-1">✓</span>}
              {s.name}
            </button>
          ))}
        </div>
        <Btn variant="secondary" onClick={() => setSetOpen(true)}>
          {t('tires.addSet')}
        </Btn>
      </div>

      {loading && <LoadingState />}
      {error && <ErrorState message={error} onRetry={reload} />}

      {data && data.length === 0 && (
        <EmptyState
          icon="🛞"
          title={t('tires.empty')}
          action={<Btn onClick={() => setSetOpen(true)}>{t('tires.addSet')}</Btn>}
        />
      )}

      {selected && (
        <div className="flex flex-col gap-5">
          <Card>
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-base font-semibold text-text">{selected.name}</span>
                    <Badge variant={selected.season === 'winter' ? 'blue' : 'green'}>
                      {seasonLabel(selected.season, t)}
                    </Badge>
                  </div>
                  <div className="text-xs text-text-muted">
                    {selected.mounted_at ? formatDate(selected.mounted_at) : '—'} ·{' '}
                    {formatKm(selected.mounted_odometer_km ?? 0)}
                  </div>
                </div>
                <WheelDiagram measurement={latestMeasurement(selected)} />
              </div>
              <Btn onClick={() => setMeasurementOpen(true)}>{t('tires.newMeasurement')}</Btn>
            </div>
          </Card>

          <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_220px]">
            <Card title={t('tires.trendTitle')}>
              {trend && trend.points.length > 0 ? (
                <>
                  <TireTrendChart trend={trend} />
                  {trend.projection_date && (
                    <p className="mt-2 text-xs text-state-red">
                      {t('tires.projectionLabel').replace('{{date}}', formatDate(trend.projection_date))}
                    </p>
                  )}
                </>
              ) : (
                <p className="py-8 text-center text-sm text-text-faint">{t('tires.noMeasurements')}</p>
              )}
            </Card>

            <div className="grid grid-cols-2 gap-3 xl:grid-cols-1">
              <StatCard label={t('tires.avgTread')} value={`${formatNumber(selected.avg_tread_mm)} mm`} color="green" />
              <StatCard label={t('tires.mileage')} value={formatKm(selected.mileage_km)} color="blue" />
              <StatCard
                label={t('tires.prediction')}
                value={selected.projection_date ? formatDate(selected.projection_date) : t('tires.noProjection')}
                color="amber"
              />
              <StatCard label={t('tires.pressure')} value={`${formatNumber(selected.avg_pressure_bar)} bar`} color="gray" />
            </div>
          </div>

          <Card title={t('tires.historyTitle')} padded>
            <Table
              columns={measurementColumns}
              rows={[...selected.measurements].sort((a, b) => +new Date(b.measured_at) - +new Date(a.measured_at))}
              rowKey={(m, i) => m.id ?? i}
              emptyMsg={t('tires.noMeasurements')}
            />
          </Card>
        </div>
      )}

      <MeasurementModal
        open={measurementOpen}
        setId={selectedId}
        defaultOdometer={currentOdometer}
        onClose={() => setMeasurementOpen(false)}
        onSaved={() => {
          setMeasurementOpen(false);
          reload();
          if (selectedId !== null) tiresApi.trend(selectedId).then(setTrend).catch(() => setTrend(null));
        }}
      />
      <TireSetModal
        open={setOpen}
        carId={carId}
        defaultOdometer={currentOdometer}
        onClose={() => setSetOpen(false)}
        onSaved={() => {
          setSetOpen(false);
          setSelectedId(null);
          reload();
        }}
      />
    </div>
  );
}

export default TiresTab;

import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { tiresApi } from '@/api/tires';
import { apiErrorMessage } from '@/api/client';
import { useApi } from '@/hooks/useApi';
import { useAuthStore } from '@/stores/authStore';
import { useUiStore } from '@/stores/uiStore';
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

/** Mean tread of a measurement (4 wheels), null-guarded. */
function measurementAvg(m: TireMeasurement): number {
  return (m.tread_fl_mm + m.tread_fr_mm + m.tread_rl_mm + m.tread_rr_mm) / 4;
}

export function TiresTab({ carId, currentOdometer }: { carId: number; currentOdometer: number }) {
  const { t } = useTranslation();
  const user = useAuthStore((s) => s.user);
  const pushToast = useUiStore((s) => s.pushToast);
  const { data, loading, error, reload } = useApi(() => tiresApi.list(carId), [carId]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [measurementOpen, setMeasurementOpen] = useState(false);
  const [editMeasurement, setEditMeasurement] = useState<TireMeasurement | null>(null);
  const [setOpen, setSetOpen] = useState(false);
  const [editSet, setEditSet] = useState<TireSet | null>(null);

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
  function loadTrend(id: number) {
    tiresApi.trend(id).then(setTrend).catch(() => setTrend(null));
  }
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

  async function setActive(set: TireSet) {
    try {
      await tiresApi.update(set.id, { is_active: true });
      pushToast(t('common.saved'), 'success');
      reload();
    } catch (err) {
      pushToast(apiErrorMessage(err), 'error');
    }
  }

  async function archive(set: TireSet) {
    try {
      await tiresApi.update(set.id, { is_active: false });
      pushToast(t('common.saved'), 'success');
      reload();
    } catch (err) {
      pushToast(apiErrorMessage(err), 'error');
    }
  }

  async function removeSet(set: TireSet) {
    if (!window.confirm(t('common.confirmDelete'))) return;
    try {
      await tiresApi.remove(set.id);
      pushToast(t('common.deleted'), 'success');
      setSelectedId(null);
      reload();
    } catch (err) {
      pushToast(apiErrorMessage(err), 'error');
    }
  }

  async function removeMeasurement(m: TireMeasurement) {
    if (!m.id || !window.confirm(t('common.confirmDelete'))) return;
    try {
      await tiresApi.removeMeasurement(m.id);
      pushToast(t('common.deleted'), 'success');
      reload();
      if (selectedId !== null) loadTrend(selectedId);
    } catch (err) {
      pushToast(apiErrorMessage(err), 'error');
    }
  }

  // Projection text: date > "≈ pri X km" > "málo dát".
  function projectionText(set: TireSet): { text: string; muted: boolean } {
    if (set.projection_date) return { text: formatDate(set.projection_date), muted: false };
    if (trend?.km_at_reference != null) {
      return { text: t('tires.projectionAtKm').replace('{{km}}', formatKm(trend.km_at_reference)), muted: false };
    }
    return { text: t('tires.fewData'), muted: true };
  }

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
      render: (m) => formatNumber(measurementAvg(m)),
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
    {
      key: 'actions',
      header: t('common.actions'),
      align: 'right',
      render: (m) => (
        <span className="flex justify-end gap-2">
          <Btn
            variant="secondary"
            size="sm"
            onClick={() => {
              setEditMeasurement(m);
              setMeasurementOpen(true);
            }}
          >
            {t('common.edit')}
          </Btn>
          <Btn variant="danger" size="sm" onClick={() => removeMeasurement(m)}>
            {t('common.delete')}
          </Btn>
        </span>
      ),
    },
  ];

  const proj = selected ? projectionText(selected) : null;
  const avgTread = selected?.avg_tread_mm;

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
              {s.name} · {seasonLabel(s.season, t)}
              {s.is_active && <span className="ml-1 text-state-green">✓</span>}
            </button>
          ))}
        </div>
        <Btn
          onClick={() => {
            setEditSet(null);
            setSetOpen(true);
          }}
        >
          {t('tires.addSet')}
        </Btn>
      </div>

      {loading && <LoadingState />}
      {error && <ErrorState message={error} onRetry={reload} />}

      {data && data.length === 0 && (
        <EmptyState
          icon="🛞"
          title={t('tires.empty')}
          action={
            <Btn
              onClick={() => {
                setEditSet(null);
                setSetOpen(true);
              }}
            >
              {t('tires.addSet')}
            </Btn>
          }
        />
      )}

      {selected && (
        <div className="flex flex-col gap-5">
          {/* Active-set header */}
          <Card>
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex-1">
                <div className="flex flex-wrap items-center gap-2 text-sm font-semibold text-text">
                  <Badge variant={selected.is_active ? 'green' : 'gray'}>
                    {selected.is_active ? t('tires.activeSet') : t('tires.inactiveSet')}
                  </Badge>
                  <span>{selected.name}</span>
                  <span className="font-normal text-text-faint">· {seasonLabel(selected.season, t)}</span>
                </div>
                <div className="mt-1 text-xs text-text-faint">
                  {t('tires.mountedAt')} {selected.mounted_at ? formatDate(selected.mounted_at) : '—'} ·{' '}
                  {formatKm(selected.mounted_odometer_km ?? 0)}
                  {selected.expected_change_date && (
                    <> · {t('tires.expectedChange')} {formatDate(selected.expected_change_date)}</>
                  )}
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  {!selected.is_active && (
                    <Btn variant="secondary" size="sm" onClick={() => setActive(selected)}>
                      {t('tires.setActive')}
                    </Btn>
                  )}
                  <Btn
                    variant="secondary"
                    size="sm"
                    onClick={() => {
                      setEditSet(selected);
                      setSetOpen(true);
                    }}
                  >
                    {t('common.edit')}
                  </Btn>
                  {selected.is_active && (
                    <Btn variant="secondary" size="sm" onClick={() => archive(selected)}>
                      {t('tires.archive')}
                    </Btn>
                  )}
                  {user?.is_admin && (
                    <Btn variant="danger" size="sm" onClick={() => removeSet(selected)}>
                      {t('common.delete')}
                    </Btn>
                  )}
                </div>
              </div>
              <WheelDiagram measurement={latestMeasurement(selected)} />
            </div>
          </Card>

          <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_220px]">
            <Card title={t('tires.trendTitle')}>
              {trend && trend.points.length >= 2 ? (
                <>
                  <TireTrendChart trend={trend} />
                  {trend.projection_date && (
                    <p className="mt-2 text-xs text-state-red">
                      {t('tires.projectionLabel').replace('{{date}}', formatDate(trend.projection_date))}
                    </p>
                  )}
                </>
              ) : (
                <p className="py-8 text-center text-sm text-text-faint">{t('tires.needTwoMeasurements')}</p>
              )}
            </Card>

            <div className="grid grid-cols-2 gap-3 xl:grid-cols-1">
              <StatCard
                label={t('tires.avgTread')}
                value={avgTread != null ? `${formatNumber(avgTread)} mm` : '—'}
                color="green"
              />
              <StatCard label={t('tires.mileage')} value={formatKm(selected.mileage_km)} color="blue" />
              <StatCard
                label={t('tires.prediction')}
                value={proj ? proj.text : '—'}
                color={proj && !proj.muted ? 'amber' : 'gray'}
              />
              <StatCard
                label={t('tires.pressure')}
                value={selected.avg_pressure_bar != null ? `${formatNumber(selected.avg_pressure_bar)} bar` : '—'}
                color="gray"
              />
            </div>
          </div>

          <Card
            title={t('tires.historyTitle')}
            actions={
              <Btn
                size="sm"
                onClick={() => {
                  setEditMeasurement(null);
                  setMeasurementOpen(true);
                }}
              >
                {t('tires.newMeasurement')}
              </Btn>
            }
          >
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
        measurement={editMeasurement}
        onClose={() => {
          setMeasurementOpen(false);
          setEditMeasurement(null);
        }}
        onSaved={() => {
          setMeasurementOpen(false);
          setEditMeasurement(null);
          reload();
          if (selectedId !== null) loadTrend(selectedId);
        }}
      />
      <TireSetModal
        open={setOpen}
        carId={carId}
        defaultOdometer={currentOdometer}
        set={editSet}
        onClose={() => {
          setSetOpen(false);
          setEditSet(null);
        }}
        onSaved={() => {
          setSetOpen(false);
          if (!editSet) setSelectedId(null);
          setEditSet(null);
          reload();
        }}
      />
    </div>
  );
}

export default TiresTab;

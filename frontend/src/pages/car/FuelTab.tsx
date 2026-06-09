import { useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { fuelApi } from '@/api/fuel';
import { apiErrorMessage } from '@/api/client';
import { useApi } from '@/hooks/useApi';
import { useUiStore } from '@/stores/uiStore';
import {
  Btn,
  Card,
  Checkbox,
  Column,
  ErrorState,
  FormField,
  Input,
  LoadingState,
  Modal,
  PeriodSelector,
  StatCard,
  Table,
  defaultPeriod,
} from '@/components/common';
import type { PeriodValue } from '@/components/common';
import { FuelBarChart } from '@/components/charts';
import { formatDate, formatKm, formatMoney, formatNumber, formatPrice, todayIso } from '@/lib/format';
import type { FuelRecord } from '@/types';

export function FuelTab({ carId, currentOdometer }: { carId: number; currentOdometer: number }) {
  const { t } = useTranslation();
  const pushToast = useUiStore((s) => s.pushToast);
  const [period, setPeriod] = useState<PeriodValue>(() => defaultPeriod());
  const range = { from_date: period.from_date, to_date: period.to_date };
  const records = useApi(() => fuelApi.list(carId, range), [carId, period.from_date, period.to_date]);
  const stats = useApi(
    () => fuelApi.stats(carId, { ...range, group_by: period.group_by }),
    [carId, period.from_date, period.to_date, period.group_by],
  );
  const [modalOpen, setModalOpen] = useState(false);

  async function remove(rec: FuelRecord) {
    if (!window.confirm(t('common.confirmDelete'))) return;
    try {
      await fuelApi.remove(rec.id);
      pushToast(t('common.deleted'), 'success');
      records.reload();
      stats.reload();
    } catch (err) {
      pushToast(apiErrorMessage(err), 'error');
    }
  }

  const columns: Column<FuelRecord>[] = [
    { key: 'date', header: t('fuel.colDate'), render: (r) => formatDate(r.refueled_at) },
    { key: 'odo', header: t('fuel.colOdometer'), align: 'right', render: (r) => formatKm(r.odometer_km) },
    { key: 'liters', header: t('fuel.colLiters'), align: 'right', render: (r) => formatNumber(r.liters, 1) },
    { key: 'price', header: t('fuel.colPrice'), align: 'right', render: (r) => formatPrice(r.price_per_liter) },
    { key: 'total', header: t('fuel.colTotal'), align: 'right', render: (r) => formatMoney(r.total_cost) },
    { key: 'full', header: t('fuel.colFull'), align: 'center', render: (r) => (r.full_tank ? '✓' : '—') },
    {
      key: 'consumption',
      header: t('fuel.colConsumption'),
      align: 'right',
      render: (r) => (r.consumption_l_100km !== null ? `${formatNumber(r.consumption_l_100km)} l` : '—'),
    },
    {
      key: 'actions',
      header: t('common.actions'),
      align: 'right',
      render: (r) => (
        <Btn variant="danger" size="sm" onClick={() => remove(r)}>
          {t('common.delete')}
        </Btn>
      ),
    },
  ];

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <PeriodSelector value={period} onChange={setPeriod} />
        <Btn onClick={() => setModalOpen(true)}>+ {t('fuel.addRecord')}</Btn>
      </div>

      <div className="mb-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard
          label={t('fuel.statAvg')}
          value={stats.data ? `${formatNumber(stats.data.avg_consumption)} l/100km` : '—'}
          color="blue"
        />
        <StatCard
          label={t('fuel.statTotal')}
          value={stats.data ? formatMoney(stats.data.total_spent) : '—'}
          color="green"
        />
        <StatCard label={t('fuel.statCount')} value={stats.data?.count ?? '—'} color="gray" />
      </div>

      <Card title={t('fuel.chartTitle')} className="mb-5">
        {stats.loading && <LoadingState />}
        {stats.error && <ErrorState message={stats.error} onRetry={stats.reload} />}
        {stats.data && stats.data.monthly.length > 0 ? (
          <FuelBarChart data={stats.data.monthly} />
        ) : (
          stats.data && <p className="py-6 text-center text-sm text-text-faint">{t('common.noData')}</p>
        )}
      </Card>

      <Card title={t('fuel.logTitle')} padded>
        {records.loading && <LoadingState />}
        {records.error && <ErrorState message={records.error} onRetry={records.reload} />}
        {records.data && (
          <Table columns={columns} rows={records.data} rowKey={(r) => r.id} emptyMsg={t('fuel.empty')} />
        )}
      </Card>

      <FuelModal
        open={modalOpen}
        carId={carId}
        defaultOdometer={currentOdometer}
        onClose={() => setModalOpen(false)}
        onSaved={() => {
          setModalOpen(false);
          records.reload();
          stats.reload();
        }}
      />
    </div>
  );
}

function FuelModal({
  open,
  carId,
  defaultOdometer,
  onClose,
  onSaved,
}: {
  open: boolean;
  carId: number;
  defaultOdometer?: number;
  onClose: () => void;
  onSaved: () => void;
}) {
  const { t } = useTranslation();
  const pushToast = useUiStore((s) => s.pushToast);
  const [refueledAt, setRefueledAt] = useState(todayIso());
  const [odometer, setOdometer] = useState(String(defaultOdometer ?? ''));
  const [liters, setLiters] = useState('');
  const [price, setPrice] = useState('');
  const [total, setTotal] = useState('');
  const [fullTank, setFullTank] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setErr(null);
    try {
      await fuelApi.create(carId, {
        refueled_at: refueledAt,
        odometer_km: Number(odometer),
        liters: Number(liters),
        price_per_liter: Number(price),
        total_cost: total ? Number(total) : null,
        full_tank: fullTank,
      });
      pushToast(t('common.created'), 'success');
      onSaved();
    } catch (e2) {
      setErr(apiErrorMessage(e2));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={t('fuel.modalTitle')} maxWidth={480}>
      <form onSubmit={submit} className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-3">
          <FormField label={t('fuel.fieldDate')} required>
            <Input type="date" value={refueledAt} onChange={(e) => setRefueledAt(e.target.value)} required />
          </FormField>
          <FormField label={t('fuel.fieldOdometer')} required>
            <Input type="number" value={odometer} onChange={(e) => setOdometer(e.target.value)} required />
          </FormField>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <FormField label={t('fuel.fieldLiters')} required>
            <Input type="number" step="0.01" value={liters} onChange={(e) => setLiters(e.target.value)} required />
          </FormField>
          <FormField label={t('fuel.fieldPrice')} required>
            <Input type="number" step="0.001" value={price} onChange={(e) => setPrice(e.target.value)} required />
          </FormField>
        </div>
        <FormField label={t('fuel.fieldTotal')}>
          <Input type="number" step="0.01" value={total} onChange={(e) => setTotal(e.target.value)} />
        </FormField>
        <Checkbox
          id="full-tank"
          label={t('fuel.fieldFull')}
          checked={fullTank}
          onChange={(e) => setFullTank(e.target.checked)}
        />

        {err && <p className="text-sm text-state-red">{err}</p>}

        <div className="mt-2 flex justify-end gap-2">
          <Btn variant="secondary" type="button" onClick={onClose}>
            {t('common.cancel')}
          </Btn>
          <Btn type="submit" disabled={submitting}>
            {submitting ? t('common.saving') : t('common.save')}
          </Btn>
        </div>
      </form>
    </Modal>
  );
}

export default FuelTab;

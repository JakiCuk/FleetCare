import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { servicesApi } from '@/api/services';
import { apiErrorMessage } from '@/api/client';
import { useApi } from '@/hooks/useApi';
import { useUiStore } from '@/stores/uiStore';
import {
  Badge,
  Btn,
  Card,
  Column,
  ErrorState,
  LoadingState,
  Table,
} from '@/components/common';
import { intervalColor, variantClasses } from '@/lib/colors';
import { formatDate, formatKm, formatMoney } from '@/lib/format';
import { cn } from '@/lib/cn';
import type { ChipVariant, ServiceCategory, ServiceInterval, ServiceRecord } from '@/types';
import { ServiceRecordModal } from './service/ServiceRecordModal';

const categoryVariant: Record<ServiceCategory, ChipVariant> = {
  service: 'blue',
  repair: 'orange',
  tires: 'green',
  other: 'gray',
};

export function ServiceTab({ carId, currentOdometer }: { carId: number; currentOdometer: number }) {
  const { t } = useTranslation();
  const pushToast = useUiStore((s) => s.pushToast);
  const records = useApi(() => servicesApi.list(carId), [carId]);
  const intervals = useApi(() => servicesApi.listIntervals(carId), [carId]);
  const [modalOpen, setModalOpen] = useState(false);

  function categoryLabel(c: ServiceCategory): string {
    return t(`service.cat${c.charAt(0).toUpperCase()}${c.slice(1)}`);
  }

  async function remove(rec: ServiceRecord) {
    if (!window.confirm(t('common.confirmDelete'))) return;
    try {
      await servicesApi.remove(rec.id);
      pushToast(t('common.deleted'), 'success');
      records.reload();
    } catch (err) {
      pushToast(apiErrorMessage(err), 'error');
    }
  }

  const columns: Column<ServiceRecord>[] = [
    { key: 'date', header: t('service.colDate'), render: (r) => formatDate(r.performed_at) },
    { key: 'odo', header: t('service.colOdometer'), align: 'right', render: (r) => formatKm(r.odometer_km) },
    { key: 'desc', header: t('service.colDescription'), render: (r) => r.description },
    {
      key: 'cat',
      header: t('service.colCategory'),
      render: (r) => <Badge variant={categoryVariant[r.category]}>{categoryLabel(r.category)}</Badge>,
    },
    { key: 'cost', header: t('service.colCost'), align: 'right', render: (r) => formatMoney(r.cost) },
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
    <div className="grid grid-cols-1 gap-5 lg:grid-cols-[1fr_300px]">
      <div>
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-text">{t('service.recordsTitle')}</h3>
          <Btn onClick={() => setModalOpen(true)}>{t('service.addRecord')}</Btn>
        </div>
        {records.loading && <LoadingState />}
        {records.error && <ErrorState message={records.error} onRetry={records.reload} />}
        {records.data && (
          <Card padded={false} className="p-2">
            <Table
              columns={columns}
              rows={records.data}
              rowKey={(r) => r.id}
              emptyMsg={t('service.empty')}
            />
          </Card>
        )}
      </div>

      <div>
        <h3 className="mb-3 text-sm font-semibold text-text">{t('service.intervalsTitle')}</h3>
        {intervals.loading && <LoadingState />}
        {intervals.error && <ErrorState message={intervals.error} onRetry={intervals.reload} />}
        {intervals.data && (
          <div className="flex flex-col gap-3">
            {intervals.data.length === 0 ? (
              <Card>
                <p className="text-center text-sm text-text-faint">{t('service.emptyIntervals')}</p>
              </Card>
            ) : (
              intervals.data.map((iv) => <IntervalCard key={iv.id} interval={iv} />)
            )}
          </div>
        )}
      </div>

      <ServiceRecordModal
        open={modalOpen}
        carId={carId}
        defaultOdometer={currentOdometer}
        onClose={() => setModalOpen(false)}
        onSaved={() => {
          setModalOpen(false);
          records.reload();
          intervals.reload();
        }}
      />
    </div>
  );
}

function IntervalCard({ interval }: { interval: ServiceInterval }) {
  const { t } = useTranslation();
  const color = intervalColor(interval.km_left, interval.days_left);

  // Progress: fraction of the interval already consumed.
  let progress = 0;
  if (interval.interval_km && interval.km_left !== null) {
    progress = Math.min(100, Math.max(0, (1 - interval.km_left / interval.interval_km) * 100));
  }

  const badgeText =
    interval.km_left !== null
      ? t('service.inKm').replace('{{count}}', String(interval.km_left))
      : interval.days_left !== null
        ? t('service.inDays').replace('{{count}}', String(interval.days_left))
        : '—';

  const barColor =
    color === 'red' ? 'bg-state-red' : color === 'yellow' ? 'bg-state-yellow' : 'bg-state-green';

  return (
    <Card padded>
      <div className="mb-2 flex items-center justify-between gap-2">
        <span className="text-[13px] font-medium text-text">{interval.name}</span>
        <span className={cn('rounded px-2 py-0.5 text-xs font-semibold', variantClasses[color])}>
          {badgeText}
        </span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-border-soft">
        <div className={cn('h-full rounded-full', barColor)} style={{ width: `${progress}%` }} />
      </div>
      <div className="mt-1 text-[11px] text-text-faint">
        {interval.next_due_km !== null && `${formatKm(interval.next_due_km)}`}
        {interval.next_due_date && ` · ${formatDate(interval.next_due_date)}`}
      </div>
    </Card>
  );
}

export default ServiceTab;

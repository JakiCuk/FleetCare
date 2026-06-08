import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { notificationsApi } from '@/api/notifications';
import { dashboardApi } from '@/api/dashboard';
import { useApi } from '@/hooks/useApi';
import {
  Badge,
  Card,
  Column,
  ErrorState,
  LoadingState,
  PageHeader,
  StatCard,
  Table,
} from '@/components/common';
import { formatDateTime } from '@/lib/format';
import { cn } from '@/lib/cn';
import type { ChipVariant, NotificationLogEntry, NotificationLogStatus } from '@/types';

type Filter = 'all' | 'sent' | 'failed';

const statusVariant: Record<NotificationLogStatus, ChipVariant> = {
  sent: 'green',
  failed: 'red',
  pending: 'yellow',
  skipped: 'gray',
};

export default function NotificationsPage() {
  const { t } = useTranslation();
  const log = useApi(() => notificationsApi.listLog({ limit: 200 }), []);
  const dashboard = useApi(() => dashboardApi.get(), []);
  const [filter, setFilter] = useState<Filter>('all');

  const filtered = useMemo(() => {
    const rows = log.data ?? [];
    if (filter === 'all') return rows;
    return rows.filter((r) => r.status === filter);
  }, [log.data, filter]);

  const counts = useMemo(() => {
    const rows = log.data ?? [];
    return {
      total: rows.length,
      sent: rows.filter((r) => r.status === 'sent').length,
      failed: rows.filter((r) => r.status === 'failed').length,
    };
  }, [log.data]);

  const overdue = dashboard.data?.stats.overdue_items ?? 0;

  const columns: Column<NotificationLogEntry>[] = [
    { key: 'time', header: t('notifications.colTime'), render: (r) => <span className="font-mono text-xs">{formatDateTime(r.sent_at)}</span> },
    { key: 'car', header: t('notifications.colCar'), render: (r) => r.car_name },
    { key: 'type', header: t('notifications.colType'), render: (r) => r.item_type },
    {
      key: 'channel',
      header: t('notifications.colChannel'),
      render: (r) => (
        <Badge variant={r.channel === 'email' ? 'blue' : 'purple'}>
          {r.channel === 'email' ? t('notifications.channelEmail') : t('notifications.channelMatrix')}
        </Badge>
      ),
    },
    { key: 'recipient', header: t('notifications.colRecipient'), render: (r) => r.recipient },
    {
      key: 'status',
      header: t('notifications.colStatus'),
      render: (r) => <Badge variant={statusVariant[r.status]}>{t(`notifications.status${r.status.charAt(0).toUpperCase()}${r.status.slice(1)}`)}</Badge>,
    },
  ];

  const filters: { key: Filter; label: string }[] = [
    { key: 'all', label: t('notifications.filterAll') },
    { key: 'sent', label: t('notifications.filterSent') },
    { key: 'failed', label: t('notifications.filterFailed') },
  ];

  return (
    <div>
      <PageHeader title={t('notifications.title')} subtitle={t('notifications.subtitle')} />

      <div className="mb-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard label={t('notifications.statTotal')} value={counts.total} color="blue" />
        <StatCard label={t('notifications.statSent')} value={counts.sent} color="green" />
        <StatCard label={t('notifications.statFailed')} value={counts.failed} color="red" />
      </div>

      {overdue > 0 && (
        <div className="mb-4 rounded-lg border border-state-red/30 bg-state-red-bg px-4 py-3 text-sm font-semibold text-state-red">
          ⚠ {t('notifications.overdueAlert').replace('{{count}}', String(overdue))}
        </div>
      )}

      <div className="mb-3 flex gap-2">
        {filters.map((f) => (
          <button
            key={f.key}
            type="button"
            onClick={() => setFilter(f.key)}
            className={cn(
              'rounded-full border px-3 py-1.5 text-[13px] font-medium transition',
              filter === f.key
                ? 'border-primary bg-primary-bg text-primary'
                : 'border-border bg-surface text-text-muted hover:bg-bg',
            )}
          >
            {f.label}
          </button>
        ))}
      </div>

      {log.loading && <LoadingState />}
      {log.error && <ErrorState message={log.error} onRetry={log.reload} />}
      {log.data && (
        <Card padded={false} className="p-2">
          <Table columns={columns} rows={filtered} rowKey={(r) => r.id} emptyMsg={t('notifications.empty')} />
        </Card>
      )}
    </div>
  );
}

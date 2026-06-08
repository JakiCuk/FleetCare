import { useTranslation } from 'react-i18next';
import { notificationsApi } from '@/api/notifications';
import { useApi } from '@/hooks/useApi';
import { Badge, Btn, Card, Column, ErrorState, LoadingState, Table } from '@/components/common';
import { formatDateTime } from '@/lib/format';
import type { ChipVariant, NotificationLogEntry, NotificationLogStatus } from '@/types';

const statusVariant: Record<NotificationLogStatus, ChipVariant> = {
  sent: 'green',
  failed: 'red',
  pending: 'yellow',
  skipped: 'gray',
};

export function LogTab() {
  const { t } = useTranslation();
  const { data, loading, error, reload } = useApi(() => notificationsApi.listLog({ limit: 200 }), []);

  const columns: Column<NotificationLogEntry>[] = [
    { key: 'time', header: t('notifications.colTime'), render: (r) => <span className="font-mono text-xs">{formatDateTime(r.sent_at)}</span> },
    { key: 'car', header: t('notifications.colCar'), render: (r) => r.car_name },
    { key: 'type', header: t('notifications.colType'), render: (r) => r.item_type },
    { key: 'channel', header: t('notifications.colChannel'), render: (r) => r.channel },
    { key: 'recipient', header: t('notifications.colRecipient'), render: (r) => r.recipient },
    {
      key: 'status',
      header: t('notifications.colStatus'),
      render: (r) => <Badge variant={statusVariant[r.status]}>{r.status}</Badge>,
    },
  ];

  return (
    <div>
      <div className="mb-3 flex justify-end">
        <a href={notificationsApi.exportCsvUrl()} target="_blank" rel="noreferrer">
          <Btn variant="secondary">{t('admin.logExport')}</Btn>
        </a>
      </div>
      {loading && <LoadingState />}
      {error && <ErrorState message={error} onRetry={reload} />}
      {data && (
        <Card padded={false} className="p-2">
          <Table columns={columns} rows={data} rowKey={(r) => r.id} emptyMsg={t('admin.logEmpty')} />
        </Card>
      )}
    </div>
  );
}

export default LogTab;

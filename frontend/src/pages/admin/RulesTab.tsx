import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { notificationsApi } from '@/api/notifications';
import { carsApi } from '@/api/cars';
import { apiErrorMessage } from '@/api/client';
import { useApi } from '@/hooks/useApi';
import { useUiStore } from '@/stores/uiStore';
import { Badge, Btn, Card, Column, ErrorState, LoadingState, Table } from '@/components/common';
import type { NotificationRule } from '@/types';
import { RuleModal, type RuleCarOption } from './RuleModal';

export function RulesTab() {
  const { t } = useTranslation();
  const pushToast = useUiStore((s) => s.pushToast);
  const { data, loading, error, reload } = useApi(() => notificationsApi.listRules(), []);

  // GET /cars is scoped server-side: admins get all cars, users only theirs.
  const carList = useApi(() => carsApi.list(), []);
  const carOptions: RuleCarOption[] = useMemo(
    () => (carList.data ?? []).map((c) => ({ id: c.id, name: c.full_name })),
    [carList.data],
  );

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<NotificationRule | null>(null);

  function openCreate() {
    setEditing(null);
    setModalOpen(true);
  }

  function openEdit(rule: NotificationRule) {
    setEditing(rule);
    setModalOpen(true);
  }

  async function toggle(rule: NotificationRule) {
    try {
      await notificationsApi.updateRule(rule.id, { is_active: !rule.is_active });
      reload();
    } catch (err) {
      pushToast(apiErrorMessage(err), 'error');
    }
  }

  async function remove(rule: NotificationRule) {
    if (!window.confirm(t('common.confirmDelete'))) return;
    try {
      await notificationsApi.removeRule(rule.id);
      pushToast(t('common.deleted'), 'success');
      reload();
    } catch (err) {
      pushToast(apiErrorMessage(err), 'error');
    }
  }

  const columns: Column<NotificationRule>[] = [
    { key: 'car', header: t('admin.rulesCar'), render: (r) => r.car_name },
    { key: 'type', header: t('admin.rulesItemType'), render: (r) => r.item_type },
    { key: 'lead1', header: t('admin.rulesLead1'), align: 'right', render: (r) => r.lead_days_1 ?? '—' },
    { key: 'lead2', header: t('admin.rulesLead2'), align: 'right', render: (r) => r.lead_days_2 ?? '—' },
    { key: 'lead3', header: t('admin.rulesLead3'), align: 'right', render: (r) => r.lead_days_3 ?? '—' },
    {
      key: 'channels',
      header: t('admin.rulesChannels'),
      render: (r) => (
        <span className="flex gap-1">
          {r.channel_email && <Badge variant="blue">✉</Badge>}
          {r.channel_matrix && <Badge variant="purple">M</Badge>}
          {r.is_smart && <Badge variant="green">{t('admin.rulesSmart')}</Badge>}
        </span>
      ),
    },
    {
      key: 'active',
      header: t('admin.rulesActive'),
      render: (r) => (
        <button type="button" onClick={() => toggle(r)}>
          <Badge variant={r.is_active ? 'green' : 'gray'}>
            {r.is_active ? t('common.active') : t('common.inactive')}
          </Badge>
        </button>
      ),
    },
    {
      key: 'actions',
      header: t('common.actions'),
      align: 'right',
      render: (r) => (
        <span className="flex justify-end gap-2">
          <Btn variant="secondary" size="sm" onClick={() => openEdit(r)}>
            {t('common.edit')}
          </Btn>
          <Btn variant="danger" size="sm" onClick={() => remove(r)}>
            {t('common.delete')}
          </Btn>
        </span>
      ),
    },
  ];

  return (
    <div>
      <div className="mb-3 flex justify-end">
        <Btn onClick={openCreate} disabled={carOptions.length === 0}>
          {t('admin.newRule')}
        </Btn>
      </div>
      {loading && <LoadingState />}
      {error && <ErrorState message={error} onRetry={reload} />}
      {data && (
        <Card padded={false} className="p-2">
          <Table columns={columns} rows={data} rowKey={(r) => r.id} emptyMsg={t('admin.rulesEmpty')} />
        </Card>
      )}

      <RuleModal
        open={modalOpen}
        cars={carOptions}
        rule={editing}
        onClose={() => setModalOpen(false)}
        onSaved={() => {
          setModalOpen(false);
          reload();
        }}
      />
    </div>
  );
}

export default RulesTab;

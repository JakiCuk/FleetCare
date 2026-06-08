import { useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { notificationsApi } from '@/api/notifications';
import { carsApi } from '@/api/cars';
import { apiErrorMessage } from '@/api/client';
import { useApi } from '@/hooks/useApi';
import { useUiStore } from '@/stores/uiStore';
import { Btn, FormField, Input, Modal, Select } from '@/components/common';
import type { NotificationChannel } from '@/types';

export function TestSendModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { t } = useTranslation();
  const pushToast = useUiStore((s) => s.pushToast);
  const cars = useApi(() => carsApi.list(), open ? [] : ['closed']);

  const [channel, setChannel] = useState<NotificationChannel>('email');
  const [carId, setCarId] = useState<string>('');
  const [to, setTo] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setErr(null);
    try {
      const res = await notificationsApi.test({
        channel,
        car_id: carId ? Number(carId) : undefined,
        to: to || undefined,
      });
      pushToast(`${t('admin.testSuccess')}: ${res.status}`, 'success');
      onClose();
    } catch (e2) {
      setErr(apiErrorMessage(e2));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={t('admin.testModalTitle')} maxWidth={440}>
      <form onSubmit={submit} className="flex flex-col gap-4">
        <FormField label={t('admin.testChannel')}>
          <Select value={channel} onChange={(e) => setChannel(e.target.value as NotificationChannel)}>
            <option value="email">{t('notifications.channelEmail')}</option>
            <option value="matrix">{t('notifications.channelMatrix')}</option>
          </Select>
        </FormField>
        <FormField label={t('admin.testCar')}>
          <Select value={carId} onChange={(e) => setCarId(e.target.value)}>
            <option value="">—</option>
            {(cars.data ?? []).map((c) => (
              <option key={c.id} value={c.id}>
                {c.full_name}
              </option>
            ))}
          </Select>
        </FormField>
        {channel === 'email' && (
          <FormField label={t('admin.testTo')}>
            <Input type="email" value={to} onChange={(e) => setTo(e.target.value)} />
          </FormField>
        )}

        {err && <p className="text-sm text-state-red">{err}</p>}

        <div className="mt-2 flex justify-end gap-2">
          <Btn variant="secondary" type="button" onClick={onClose}>
            {t('common.cancel')}
          </Btn>
          <Btn type="submit" disabled={submitting}>
            {submitting ? t('common.saving') : t('admin.testSubmit')}
          </Btn>
        </div>
      </form>
    </Modal>
  );
}

export default TestSendModal;

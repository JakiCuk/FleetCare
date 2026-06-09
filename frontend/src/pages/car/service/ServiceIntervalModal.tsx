import { useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { servicesApi } from '@/api/services';
import { apiErrorMessage } from '@/api/client';
import { useUiStore } from '@/stores/uiStore';
import { Btn, FormField, Input, Modal } from '@/components/common';
import type { CreateServiceIntervalRequest, ServiceInterval } from '@/types';

interface ServiceIntervalModalProps {
  open: boolean;
  carId: number;
  interval?: ServiceInterval | null;
  onClose: () => void;
  onSaved: () => void;
}

export function ServiceIntervalModal({ open, carId, interval, onClose, onSaved }: ServiceIntervalModalProps) {
  const { t } = useTranslation();
  const pushToast = useUiStore((s) => s.pushToast);
  const editing = !!interval;

  const [name, setName] = useState('');
  const [intervalKm, setIntervalKm] = useState('');
  const [intervalMonths, setIntervalMonths] = useState('');
  const [lastKm, setLastKm] = useState('');
  const [lastAt, setLastAt] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    if (interval) {
      setName(interval.name);
      setIntervalKm(interval.interval_km != null ? String(interval.interval_km) : '');
      setIntervalMonths(interval.interval_months != null ? String(interval.interval_months) : '');
      setLastKm(interval.last_performed_km != null ? String(interval.last_performed_km) : '');
      setLastAt(interval.last_performed_at ?? '');
    } else {
      setName('');
      setIntervalKm('');
      setIntervalMonths('');
      setLastKm('');
      setLastAt('');
    }
    setErr(null);
  }, [open, interval]);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setErr(null);
    const body: CreateServiceIntervalRequest = {
      name,
      interval_km: intervalKm ? Number(intervalKm) : null,
      interval_months: intervalMonths ? Number(intervalMonths) : null,
      last_performed_km: lastKm ? Number(lastKm) : null,
      last_performed_at: lastAt || null,
    };
    try {
      if (editing && interval) {
        await servicesApi.updateInterval(interval.id, body);
        pushToast(t('common.saved'), 'success');
      } else {
        await servicesApi.createInterval(carId, body);
        pushToast(t('common.created'), 'success');
      }
      onSaved();
    } catch (e2) {
      setErr(apiErrorMessage(e2));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={editing ? t('service.editIntervalTitle') : t('service.addIntervalTitle')}
      maxWidth={440}
    >
      <form onSubmit={submit} className="flex flex-col gap-4">
        <FormField label={t('service.intervalName')} required>
          <Input value={name} onChange={(e) => setName(e.target.value)} required />
        </FormField>
        <div className="grid grid-cols-2 gap-3">
          <FormField label={t('service.intervalKm')}>
            <Input type="number" value={intervalKm} onChange={(e) => setIntervalKm(e.target.value)} />
          </FormField>
          <FormField label={t('service.intervalMonths')}>
            <Input type="number" value={intervalMonths} onChange={(e) => setIntervalMonths(e.target.value)} />
          </FormField>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <FormField label={t('service.lastPerformedKm')}>
            <Input type="number" value={lastKm} onChange={(e) => setLastKm(e.target.value)} />
          </FormField>
          <FormField label={t('service.lastPerformedAt')}>
            <Input type="date" value={lastAt} onChange={(e) => setLastAt(e.target.value)} />
          </FormField>
        </div>

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

export default ServiceIntervalModal;

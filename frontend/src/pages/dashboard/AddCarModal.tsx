import { useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { carsApi } from '@/api/cars';
import { apiErrorMessage } from '@/api/client';
import { useUiStore } from '@/stores/uiStore';
import { Btn, FormField, Input, Modal } from '@/components/common';
import type { Car } from '@/types';

interface AddCarModalProps {
  open: boolean;
  onClose: () => void;
  onCreated: (car: Car) => void;
}

export function AddCarModal({ open, onClose, onCreated }: AddCarModalProps) {
  const { t } = useTranslation();
  const pushToast = useUiStore((s) => s.pushToast);

  const [form, setForm] = useState({
    make: '',
    model: '',
    year: new Date().getFullYear(),
    license_plate: '',
    vin: '',
    current_odometer_km: 0,
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function set<K extends keyof typeof form>(key: K, value: (typeof form)[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const car = await carsApi.create(form);
      pushToast(t('common.created'), 'success');
      onCreated(car);
      onClose();
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={t('addCar.title')} maxWidth={520}>
      <form onSubmit={onSubmit} className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-3">
          <FormField label={t('addCar.make')} required>
            <Input value={form.make} onChange={(e) => set('make', e.target.value)} required />
          </FormField>
          <FormField label={t('addCar.model')} required>
            <Input value={form.model} onChange={(e) => set('model', e.target.value)} required />
          </FormField>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <FormField label={t('addCar.year')}>
            <Input
              type="number"
              value={form.year}
              onChange={(e) => set('year', Number(e.target.value))}
            />
          </FormField>
          <FormField label={t('addCar.licensePlate')} required>
            <Input
              value={form.license_plate}
              onChange={(e) => set('license_plate', e.target.value)}
              className="font-mono"
              required
            />
          </FormField>
        </div>
        <FormField label={t('addCar.vin')}>
          <Input
            value={form.vin}
            onChange={(e) => set('vin', e.target.value)}
            className="font-mono"
          />
        </FormField>
        <FormField label={t('addCar.odometer')}>
          <Input
            type="number"
            value={form.current_odometer_km}
            onChange={(e) => set('current_odometer_km', Number(e.target.value))}
          />
        </FormField>

        {error && <p className="text-sm text-state-red">{error}</p>}

        <div className="mt-2 flex justify-end gap-2">
          <Btn variant="secondary" onClick={onClose} type="button">
            {t('common.cancel')}
          </Btn>
          <Btn type="submit" disabled={submitting}>
            {submitting ? t('common.saving') : t('addCar.submit')}
          </Btn>
        </div>
      </form>
    </Modal>
  );
}

export default AddCarModal;

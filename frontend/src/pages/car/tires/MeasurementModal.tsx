import { useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { tiresApi } from '@/api/tires';
import { apiErrorMessage } from '@/api/client';
import { useUiStore } from '@/stores/uiStore';
import { Btn, FormField, Input, Modal } from '@/components/common';
import { todayIso } from '@/lib/format';
import type { TireMeasurement } from '@/types';

const WHEELS = ['fl', 'fr', 'rl', 'rr'] as const;
type Wheel = (typeof WHEELS)[number];

interface MeasurementModalProps {
  open: boolean;
  setId: number | null;
  defaultOdometer?: number;
  onClose: () => void;
  onSaved: () => void;
}

const emptyTread: Record<Wheel, string> = { fl: '', fr: '', rl: '', rr: '' };
const emptyPressure: Record<Wheel, string> = { fl: '', fr: '', rl: '', rr: '' };

export function MeasurementModal({
  open,
  setId,
  defaultOdometer,
  onClose,
  onSaved,
}: MeasurementModalProps) {
  const { t } = useTranslation();
  const pushToast = useUiStore((s) => s.pushToast);

  const [measuredAt, setMeasuredAt] = useState(todayIso());
  const [odometer, setOdometer] = useState(String(defaultOdometer ?? ''));
  const [tread, setTread] = useState<Record<Wheel, string>>({ ...emptyTread });
  const [pBefore, setPBefore] = useState<Record<Wheel, string>>({ ...emptyPressure });
  const [pAfter, setPAfter] = useState<Record<Wheel, string>>({ ...emptyPressure });
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const num = (v: string): number | null => (v === '' ? null : Number(v));

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (setId === null) return;
    setSubmitting(true);
    setErr(null);
    const body: TireMeasurement = {
      measured_at: measuredAt,
      odometer_km: Number(odometer),
      tread_fl_mm: Number(tread.fl),
      tread_fr_mm: Number(tread.fr),
      tread_rl_mm: Number(tread.rl),
      tread_rr_mm: Number(tread.rr),
      pressure_fl_before_bar: num(pBefore.fl),
      pressure_fr_before_bar: num(pBefore.fr),
      pressure_rl_before_bar: num(pBefore.rl),
      pressure_rr_before_bar: num(pBefore.rr),
      pressure_fl_after_bar: num(pAfter.fl),
      pressure_fr_after_bar: num(pAfter.fr),
      pressure_rl_after_bar: num(pAfter.rl),
      pressure_rr_after_bar: num(pAfter.rr),
    };
    try {
      await tiresApi.addMeasurement(setId, body);
      pushToast(t('common.created'), 'success');
      onSaved();
    } catch (e2) {
      setErr(apiErrorMessage(e2));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={t('tires.measurementModalTitle')} maxWidth={560}>
      <form onSubmit={submit} className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-3">
          <FormField label={t('tires.measuredAt')} required>
            <Input type="date" value={measuredAt} onChange={(e) => setMeasuredAt(e.target.value)} required />
          </FormField>
          <FormField label={t('tires.odometerKm')} required>
            <Input type="number" value={odometer} onChange={(e) => setOdometer(e.target.value)} required />
          </FormField>
        </div>

        <div>
          <div className="mb-2 text-[13px] font-semibold text-text">{t('tires.treadSection')}</div>
          <div className="grid grid-cols-4 gap-2">
            {WHEELS.map((w) => (
              <FormField key={w} label={t(`tires.wheel${w.toUpperCase()}`)}>
                <Input
                  type="number"
                  step="0.1"
                  value={tread[w]}
                  onChange={(e) => setTread((s) => ({ ...s, [w]: e.target.value }))}
                  required
                />
              </FormField>
            ))}
          </div>
        </div>

        <div>
          <div className="mb-2 text-[13px] font-semibold text-text">{t('tires.pressureSection')}</div>
          <table className="w-full text-[13px]">
            <thead>
              <tr className="text-xs text-text-muted">
                <th className="text-left font-medium">{t('tires.wheel')}</th>
                <th className="font-medium">{t('tires.before')}</th>
                <th className="font-medium">{t('tires.after')}</th>
              </tr>
            </thead>
            <tbody>
              {WHEELS.map((w) => (
                <tr key={w}>
                  <td className="py-1 font-medium">{t(`tires.wheel${w.toUpperCase()}`)}</td>
                  <td className="px-1 py-1">
                    <Input
                      type="number"
                      step="0.1"
                      value={pBefore[w]}
                      onChange={(e) => setPBefore((s) => ({ ...s, [w]: e.target.value }))}
                    />
                  </td>
                  <td className="px-1 py-1">
                    <Input
                      type="number"
                      step="0.1"
                      value={pAfter[w]}
                      onChange={(e) => setPAfter((s) => ({ ...s, [w]: e.target.value }))}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
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

export default MeasurementModal;

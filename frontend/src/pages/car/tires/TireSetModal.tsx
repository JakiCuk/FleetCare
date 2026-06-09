import { useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { tiresApi } from '@/api/tires';
import { apiErrorMessage } from '@/api/client';
import { useUiStore } from '@/stores/uiStore';
import { Btn, FormField, Input, Modal, Select } from '@/components/common';
import { todayIso } from '@/lib/format';
import type { CreateTireSetRequest, TireMeasurement, TireSeason, TireSet } from '@/types';

const WHEELS = ['fl', 'fr', 'rl', 'rr'] as const;
type Wheel = (typeof WHEELS)[number];

interface TireSetModalProps {
  open: boolean;
  carId: number;
  defaultOdometer?: number;
  /** Existing set to edit (metadata only); null for create. */
  set?: TireSet | null;
  onClose: () => void;
  onSaved: () => void;
}

export function TireSetModal({ open, carId, defaultOdometer, set, onClose, onSaved }: TireSetModalProps) {
  const { t } = useTranslation();
  const pushToast = useUiStore((s) => s.pushToast);
  const editing = !!set;

  const [name, setName] = useState('');
  const [season, setSeason] = useState<TireSeason>('summer');
  const [mountedAt, setMountedAt] = useState(todayIso());
  const [mountedOdometer, setMountedOdometer] = useState(String(defaultOdometer ?? ''));
  const [expectedChange, setExpectedChange] = useState('');
  const [tread, setTread] = useState<Record<Wheel, string>>({ fl: '', fr: '', rl: '', rr: '' });
  const [pressure, setPressure] = useState<Record<Wheel, string>>({ fl: '', fr: '', rl: '', rr: '' });
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  // Sync form when the modal opens (create defaults vs. edit prefill).
  useEffect(() => {
    if (!open) return;
    if (set) {
      setName(set.name);
      setSeason(set.season);
      setMountedAt(set.mounted_at ?? todayIso());
      setMountedOdometer(set.mounted_odometer_km != null ? String(set.mounted_odometer_km) : '');
      setExpectedChange(set.expected_change_date ?? '');
    } else {
      setName('');
      setSeason('summer');
      setMountedAt(todayIso());
      setMountedOdometer(String(defaultOdometer ?? ''));
      setExpectedChange('');
      setTread({ fl: '', fr: '', rl: '', rr: '' });
      setPressure({ fl: '', fr: '', rl: '', rr: '' });
    }
    setErr(null);
  }, [open, set, defaultOdometer]);

  const num = (v: string): number | null => (v === '' ? null : Number(v));

  async function submit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setErr(null);

    try {
      if (editing && set) {
        await tiresApi.update(set.id, {
          name,
          season,
          mounted_at: mountedAt || null,
          mounted_odometer_km: mountedOdometer ? Number(mountedOdometer) : null,
          expected_change_date: expectedChange || null,
        });
        pushToast(t('common.saved'), 'success');
        onSaved();
        return;
      }

      const hasTread = WHEELS.every((w) => tread[w] !== '');
      let initial: TireMeasurement | undefined;
      if (hasTread) {
        initial = {
          measured_at: mountedAt,
          odometer_km: Number(mountedOdometer || 0),
          tread_fl_mm: Number(tread.fl),
          tread_fr_mm: Number(tread.fr),
          tread_rl_mm: Number(tread.rl),
          tread_rr_mm: Number(tread.rr),
          pressure_fl_after_bar: num(pressure.fl),
          pressure_fr_after_bar: num(pressure.fr),
          pressure_rl_after_bar: num(pressure.rl),
          pressure_rr_after_bar: num(pressure.rr),
        };
      }

      const body: CreateTireSetRequest = {
        name,
        season,
        mounted_at: mountedAt,
        mounted_odometer_km: mountedOdometer ? Number(mountedOdometer) : null,
        expected_change_date: expectedChange || null,
        initial_measurement: initial,
      };
      await tiresApi.create(carId, body);
      pushToast(t('common.created'), 'success');
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
      title={editing ? t('tires.editSetTitle') : t('tires.setModalTitle')}
      maxWidth={540}
    >
      <form onSubmit={submit} className="flex flex-col gap-4">
        {!editing && (
          <div className="rounded-lg border border-state-blue/30 bg-state-blue-bg px-3.5 py-2.5 text-[13px] text-state-blue">
            {t('tires.setInfo')}
          </div>
        )}

        <FormField label={t('tires.setName')} required>
          <Input value={name} onChange={(e) => setName(e.target.value)} required />
        </FormField>
        <div className="grid grid-cols-2 gap-3">
          <FormField label={t('tires.season')}>
            <Select value={season} onChange={(e) => setSeason(e.target.value as TireSeason)}>
              <option value="summer">{t('tires.seasonSummer')}</option>
              <option value="winter">{t('tires.seasonWinter')}</option>
              <option value="all_season">{t('tires.seasonAllseason')}</option>
            </Select>
          </FormField>
          <FormField label={t('tires.mountedAt')}>
            <Input type="date" value={mountedAt} onChange={(e) => setMountedAt(e.target.value)} />
          </FormField>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <FormField label={t('tires.mountedOdometer')}>
            <Input type="number" value={mountedOdometer} onChange={(e) => setMountedOdometer(e.target.value)} />
          </FormField>
          <FormField label={t('tires.expectedChange')}>
            <Input type="date" value={expectedChange} onChange={(e) => setExpectedChange(e.target.value)} />
          </FormField>
        </div>

        {!editing && (
          <>
            <div>
              <div className="mb-2 text-[13px] font-semibold text-text">
                {t('tires.initialTread')} ({t('tires.treadSection')})
              </div>
              <div className="grid grid-cols-4 gap-2">
                {WHEELS.map((w) => (
                  <FormField key={w} label={t(`tires.wheel${w.toUpperCase()}`)}>
                    <Input
                      type="number"
                      step="0.1"
                      value={tread[w]}
                      onChange={(e) => setTread((st) => ({ ...st, [w]: e.target.value }))}
                    />
                  </FormField>
                ))}
              </div>
            </div>

            <div>
              <div className="mb-2 text-[13px] font-semibold text-text">{t('tires.pressureSection')}</div>
              <div className="grid grid-cols-4 gap-2">
                {WHEELS.map((w) => (
                  <FormField key={w} label={t(`tires.wheel${w.toUpperCase()}`)}>
                    <Input
                      type="number"
                      step="0.1"
                      value={pressure[w]}
                      onChange={(e) => setPressure((st) => ({ ...st, [w]: e.target.value }))}
                    />
                  </FormField>
                ))}
              </div>
            </div>
          </>
        )}

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

export default TireSetModal;

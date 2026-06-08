import { useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { servicesApi } from '@/api/services';
import { apiErrorMessage } from '@/api/client';
import { useUiStore } from '@/stores/uiStore';
import { Btn, Checkbox, FormField, Input, Modal, Select, Textarea } from '@/components/common';
import { todayIso } from '@/lib/format';
import { cn } from '@/lib/cn';
import type { CreateServiceRecordRequest, ServiceCategory } from '@/types';

interface ServiceRecordModalProps {
  open: boolean;
  carId: number;
  defaultOdometer?: number;
  onClose: () => void;
  onSaved: () => void;
}

const CATEGORY_CHIPS: { key: ServiceCategory; icon: string; labelKey: string }[] = [
  { key: 'service', icon: '🔵', labelKey: 'service.catService' },
  { key: 'repair', icon: '🟠', labelKey: 'service.catRepair' },
  { key: 'tires', icon: '🟢', labelKey: 'service.catTires' },
  { key: 'other', icon: '⚪', labelKey: 'service.catOther' },
];

// Predefined "Vykonané" checklist items (i18n keys).
const PERFORMED_ITEMS = [
  'service.itemOil',
  'service.itemOilFilter',
  'service.itemAirFilter',
  'service.itemCabinFilter',
  'service.itemFuelFilter',
  'service.itemSparkPlugs',
  'service.itemBrakeFluid',
  'service.itemBrakePads',
  'service.itemWipers',
  'service.itemCoolant',
];

export function ServiceRecordModal({
  open,
  carId,
  defaultOdometer,
  onClose,
  onSaved,
}: ServiceRecordModalProps) {
  const { t } = useTranslation();
  const pushToast = useUiStore((s) => s.pushToast);

  const [category, setCategory] = useState<ServiceCategory>('service');
  const [performedAt, setPerformedAt] = useState(todayIso());
  const [odometer, setOdometer] = useState(String(defaultOdometer ?? ''));
  const [description, setDescription] = useState('');
  const [cost, setCost] = useState('');

  // Servis extended panel
  const [performed, setPerformed] = useState<Record<string, boolean>>({});
  const [additionalWork, setAdditionalWork] = useState<Record<string, boolean>>({});
  const [customItems, setCustomItems] = useState<string[]>([]);
  const [oilName, setOilName] = useState('');
  const [nextOilKm, setNextOilKm] = useState('');
  const [nextServiceDate, setNextServiceDate] = useState('');
  const [nextServiceKm, setNextServiceKm] = useState('');
  const [nextAdditionalDate, setNextAdditionalDate] = useState('');
  const [nextAdditionalKm, setNextAdditionalKm] = useState('');
  const [defectFound, setDefectFound] = useState(false);
  const [defectDescription, setDefectDescription] = useState('');
  const [createReminder, setCreateReminder] = useState(false);

  // Repair panel
  const [shop, setShop] = useState('');
  const [warrantyUntil, setWarrantyUntil] = useState('');
  const [partsList, setPartsList] = useState('');

  // Tires panel
  const [tireAction, setTireAction] = useState('');
  const [season, setSeason] = useState('');

  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  function resetExtended() {
    setPerformed({});
    setAdditionalWork({});
    setCustomItems([]);
  }

  function buildBody(): CreateServiceRecordRequest {
    const base: CreateServiceRecordRequest = {
      performed_at: performedAt,
      odometer_km: Number(odometer),
      category,
      description,
      cost: cost ? Number(cost) : null,
    };

    if (category === 'service') {
      const performedKeys = Object.entries(performed)
        .filter(([, v]) => v)
        .map(([k]) => t(k));
      const additionalKeys = Object.entries(additionalWork)
        .filter(([, v]) => v)
        .map(([k]) => t(k));
      base.performed_items = [...performedKeys, ...customItems.filter(Boolean)];
      base.additional_work = additionalKeys;
      base.oil_name = oilName || null;
      base.next_oil_change_km = nextOilKm ? Number(nextOilKm) : null;
      base.next_service_date = nextServiceDate || null;
      base.next_service_km = nextServiceKm ? Number(nextServiceKm) : null;
      base.next_additional_date = nextAdditionalDate || null;
      base.next_additional_km = nextAdditionalKm ? Number(nextAdditionalKm) : null;
      base.defect_found = defectFound;
      base.defect_description = defectFound ? defectDescription || null : null;
      base.create_reminder = createReminder;
    } else if (category === 'repair') {
      base.shop = shop || null;
      base.warranty_until = warrantyUntil || null;
      base.additional_work = partsList ? partsList.split('\n').filter(Boolean) : [];
    } else if (category === 'tires') {
      base.tire_action = tireAction || null;
      base.season = season || null;
    }
    return base;
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setErr(null);
    try {
      await servicesApi.create(carId, buildBody());
      pushToast(t('common.created'), 'success');
      onSaved();
    } catch (e2) {
      setErr(apiErrorMessage(e2));
    } finally {
      setSubmitting(false);
    }
  }

  const wide = category === 'service';

  return (
    <Modal open={open} onClose={onClose} title={t('service.modalTitle')} maxWidth={wide ? 720 : 480}>
      <form onSubmit={submit} className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-3">
          <FormField label={t('service.fieldDate')} required>
            <Input type="date" value={performedAt} onChange={(e) => setPerformedAt(e.target.value)} required />
          </FormField>
          <FormField label={t('service.fieldOdometer')} required>
            <Input type="number" value={odometer} onChange={(e) => setOdometer(e.target.value)} required />
          </FormField>
        </div>

        <FormField label={t('service.fieldCategory')}>
          <div className="flex flex-wrap gap-2">
            {CATEGORY_CHIPS.map((chip) => (
              <button
                key={chip.key}
                type="button"
                onClick={() => {
                  setCategory(chip.key);
                  resetExtended();
                }}
                className={cn(
                  'flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-[13px] font-medium transition',
                  category === chip.key
                    ? 'border-primary bg-primary-bg text-primary'
                    : 'border-border bg-surface text-text-muted hover:bg-bg',
                )}
              >
                <span>{chip.icon}</span>
                {t(chip.labelKey)}
              </button>
            ))}
          </div>
        </FormField>

        <FormField label={t('service.fieldDescription')}>
          <Textarea value={description} onChange={(e) => setDescription(e.target.value)} />
        </FormField>

        {/* ── Servis extended panel ── */}
        {category === 'service' && (
          <div className="rounded-lg border border-border bg-bg/40 p-4">
            <div className="mb-3 text-[13px] font-semibold text-text">{t('service.confirmationTitle')}</div>

            <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
              <div>
                <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-text-muted">
                  {t('service.performed')}
                </div>
                <div className="flex flex-col gap-1.5">
                  {PERFORMED_ITEMS.map((key) => (
                    <Checkbox
                      key={key}
                      id={`perf-${key}`}
                      label={t(key)}
                      checked={!!performed[key]}
                      onChange={(e) => setPerformed((s) => ({ ...s, [key]: e.target.checked }))}
                    />
                  ))}
                </div>
              </div>

              <div>
                <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-text-muted">
                  {t('service.additionalWork')}
                </div>
                <div className="flex flex-col gap-1.5">
                  {PERFORMED_ITEMS.map((key) => (
                    <Checkbox
                      key={key}
                      id={`add-${key}`}
                      label={t(key)}
                      checked={!!additionalWork[key]}
                      onChange={(e) => setAdditionalWork((s) => ({ ...s, [key]: e.target.checked }))}
                    />
                  ))}
                </div>
                <div className="mt-3 flex flex-col gap-2">
                  {customItems.map((item, i) => (
                    <div key={i} className="flex items-center gap-2">
                      <Input
                        value={item}
                        onChange={(e) =>
                          setCustomItems((arr) => arr.map((v, j) => (j === i ? e.target.value : v)))
                        }
                      />
                      <button
                        type="button"
                        aria-label="remove"
                        className="flex h-7 w-7 items-center justify-center rounded text-state-red hover:bg-state-red-bg"
                        onClick={() => setCustomItems((arr) => arr.filter((_, j) => j !== i))}
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                  <button
                    type="button"
                    className="self-start text-[13px] font-medium text-primary hover:underline"
                    onClick={() => setCustomItems((arr) => [...arr, ''])}
                  >
                    {t('service.addItem')}
                  </button>
                </div>
              </div>
            </div>

            <div className="mt-4 grid grid-cols-2 gap-3">
              <FormField label={t('service.oilName')}>
                <Input value={oilName} onChange={(e) => setOilName(e.target.value)} />
              </FormField>
              <FormField label={t('service.nextOilChange')}>
                <Input type="number" value={nextOilKm} onChange={(e) => setNextOilKm(e.target.value)} />
              </FormField>
            </div>

            <div className="mt-4">
              <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-text-muted">
                {t('service.furtherTerms')}
              </div>
              <div className="flex flex-col gap-3">
                <div className="grid grid-cols-[1fr_auto_auto] items-end gap-2">
                  <span className="text-[13px] text-text">{t('service.serviceCheck')}</span>
                  <FormField label={t('service.termDate')}>
                    <Input type="date" value={nextServiceDate} onChange={(e) => setNextServiceDate(e.target.value)} />
                  </FormField>
                  <FormField label={t('service.termKm')}>
                    <Input type="number" value={nextServiceKm} onChange={(e) => setNextServiceKm(e.target.value)} />
                  </FormField>
                </div>
                <div className="grid grid-cols-[1fr_auto_auto] items-end gap-2">
                  <span className="text-[13px] text-text">{t('service.additionalTerm')}</span>
                  <FormField label={t('service.termDate')}>
                    <Input type="date" value={nextAdditionalDate} onChange={(e) => setNextAdditionalDate(e.target.value)} />
                  </FormField>
                  <FormField label={t('service.termKm')}>
                    <Input type="number" value={nextAdditionalKm} onChange={(e) => setNextAdditionalKm(e.target.value)} />
                  </FormField>
                </div>
              </div>
            </div>

            <div className="mt-4">
              <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-text-muted">
                {t('service.bodyCheck')}
              </div>
              <div className="flex items-center gap-4">
                <span className="text-[13px] text-text">{t('service.defectFound')}</span>
                <Checkbox id="defect-yes" label={t('common.yes')} checked={defectFound} onChange={() => setDefectFound(true)} />
                <Checkbox id="defect-no" label={t('common.no')} checked={!defectFound} onChange={() => setDefectFound(false)} />
              </div>
              {defectFound && (
                <FormField className="mt-2" label={t('service.defectDescription')}>
                  <Textarea value={defectDescription} onChange={(e) => setDefectDescription(e.target.value)} />
                </FormField>
              )}
            </div>

            <div className="mt-4">
              <Checkbox
                id="create-reminder"
                label={t('service.createReminder')}
                checked={createReminder}
                onChange={(e) => setCreateReminder(e.target.checked)}
              />
            </div>
          </div>
        )}

        {/* ── Repair panel ── */}
        {category === 'repair' && (
          <div className="grid grid-cols-2 gap-3 rounded-lg border border-border bg-bg/40 p-4">
            <FormField label={t('service.repairShop')}>
              <Input value={shop} onChange={(e) => setShop(e.target.value)} />
            </FormField>
            <FormField label={t('service.warrantyUntil')}>
              <Input type="date" value={warrantyUntil} onChange={(e) => setWarrantyUntil(e.target.value)} />
            </FormField>
            <FormField className="col-span-2" label={t('service.partsList')}>
              <Textarea value={partsList} onChange={(e) => setPartsList(e.target.value)} />
            </FormField>
          </div>
        )}

        {/* ── Tires panel ── */}
        {category === 'tires' && (
          <div className="grid grid-cols-2 gap-3 rounded-lg border border-border bg-bg/40 p-4">
            <FormField label={t('service.tireAction')}>
              <Input value={tireAction} onChange={(e) => setTireAction(e.target.value)} />
            </FormField>
            <FormField label={t('service.tireSeason')}>
              <Select value={season} onChange={(e) => setSeason(e.target.value)}>
                <option value="">—</option>
                <option value="summer">{t('tires.seasonSummer')}</option>
                <option value="winter">{t('tires.seasonWinter')}</option>
                <option value="all_season">{t('tires.seasonAllseason')}</option>
              </Select>
            </FormField>
          </div>
        )}

        <FormField label={t('service.fieldCost')}>
          <Input type="number" value={cost} onChange={(e) => setCost(e.target.value)} />
        </FormField>

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

export default ServiceRecordModal;

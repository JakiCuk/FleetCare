import { useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { servicesApi } from '@/api/services';
import { apiErrorMessage } from '@/api/client';
import { useUiStore } from '@/stores/uiStore';
import { Btn, FormField, Input, Modal, Select, Textarea } from '@/components/common';
import { todayIso } from '@/lib/format';
import { cn } from '@/lib/cn';
import type { CreateServiceRecordRequest, ServiceCategory, ServiceRecord } from '@/types';

interface ServiceRecordModalProps {
  open: boolean;
  carId: number;
  defaultOdometer?: number;
  /** Existing record to edit/view; null for a new one. */
  record?: ServiceRecord | null;
  onClose: () => void;
  onSaved: () => void;
}

const CATEGORY_CHIPS: {
  key: ServiceCategory;
  labelKey: string;
  active: string;
  bg: string;
}[] = [
  { key: 'service', labelKey: 'service.catService', active: 'border-state-blue text-state-blue', bg: 'bg-state-blue-bg' },
  { key: 'repair', labelKey: 'service.catRepair', active: 'border-state-orange text-state-orange', bg: 'bg-state-orange-bg' },
  { key: 'tires', labelKey: 'service.catTires', active: 'border-state-green text-state-green', bg: 'bg-state-green-bg' },
  { key: 'other', labelKey: 'service.catOther', active: 'border-state-gray text-state-gray', bg: 'bg-state-gray-bg' },
];

// Service-book "Vykonané" (performed) checklist — i18n keys; first two emphasized.
const PERFORMED_ITEMS: { key: string; emphasis?: boolean }[] = [
  { key: 'service.performed.oilChangeService', emphasis: true },
  { key: 'service.performed.inspection', emphasis: true },
  { key: 'service.performed.withOilChange' },
  { key: 'service.performed.extendedScope' },
  { key: 'service.performed.longlifeOil' },
  { key: 'service.performed.cngCorrosion' },
  { key: 'service.performed.headlights' },
  { key: 'service.performed.repairRec' },
  { key: 'service.performed.customerRequest' },
];

// Service-book "Dodatočné práce – výmena" (additional replacement work).
const ADDITIONAL_WORK = [
  'service.additional.adblue',
  'service.additional.brakeFluid',
  'service.additional.fuelFilter',
  'service.additional.gearOil',
  'service.additional.haldex',
  'service.additional.serpentine',
  'service.additional.airFilter',
  'service.additional.tyreSealant',
  'service.additional.cabinFilter',
  'service.additional.timingBelt',
  'service.additional.sparkPlugs',
];

const TIRE_ACTIONS = ['seasonalChange', 'balancing', 'geometry', 'punctureRepair', 'other'] as const;

function CheckItem({
  label,
  checked,
  onChange,
  emphasis,
}: {
  label: string;
  checked: boolean;
  onChange: () => void;
  emphasis?: boolean;
}) {
  return (
    <label
      className={cn(
        'flex cursor-pointer items-start gap-2 py-1 text-[13px] leading-snug text-text',
        emphasis && 'font-semibold',
      )}
    >
      <input
        type="checkbox"
        checked={checked}
        onChange={onChange}
        className="mt-0.5 h-4 w-4 shrink-0 rounded border-[#d1d5db] text-primary focus:ring-primary/30"
      />
      <span>{label}</span>
    </label>
  );
}

export function ServiceRecordModal({
  open,
  carId,
  defaultOdometer,
  record,
  onClose,
  onSaved,
}: ServiceRecordModalProps) {
  const { t } = useTranslation();
  const pushToast = useUiStore((s) => s.pushToast);
  const editing = !!record;

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
  const [serviceByIndicator, setServiceByIndicator] = useState(false);
  const [nextServiceDate, setNextServiceDate] = useState('');
  const [nextServiceKm, setNextServiceKm] = useState('');
  const [nextAdditionalDesc, setNextAdditionalDesc] = useState('');
  const [nextAdditionalDate, setNextAdditionalDate] = useState('');
  const [nextAdditionalKm, setNextAdditionalKm] = useState('');
  const [defect, setDefect] = useState<'yes' | 'no' | null>(null);
  const [defectDescription, setDefectDescription] = useState('');
  const [createReminder, setCreateReminder] = useState(true);

  // Repair panel
  const [shop, setShop] = useState('');
  const [warrantyUntil, setWarrantyUntil] = useState('');
  const [partsList, setPartsList] = useState('');

  // Tires panel
  const [tireAction, setTireAction] = useState('seasonalChange');
  const [season, setSeason] = useState('winter');

  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  function resetAll() {
    setCategory('service');
    setPerformedAt(todayIso());
    setOdometer(String(defaultOdometer ?? ''));
    setDescription('');
    setCost('');
    setPerformed({});
    setAdditionalWork({});
    setCustomItems([]);
    setOilName('');
    setNextOilKm('');
    setServiceByIndicator(false);
    setNextServiceDate('');
    setNextServiceKm('');
    setNextAdditionalDesc('');
    setNextAdditionalDate('');
    setNextAdditionalKm('');
    setDefect(null);
    setDefectDescription('');
    setCreateReminder(true);
    setShop('');
    setWarrantyUntil('');
    setPartsList('');
    setTireAction('seasonalChange');
    setSeason('winter');
  }

  // Sync form when the modal opens (create defaults vs. edit prefill).
  useEffect(() => {
    if (!open) return;
    if (record) {
      setCategory(record.category);
      setPerformedAt(record.performed_at);
      setOdometer(String(record.odometer_km));
      setDescription(record.description ?? '');
      setCost(record.cost != null ? String(record.cost) : '');
      // Map saved performed/additional labels back to checkbox keys.
      const perfMap: Record<string, boolean> = {};
      const custom: string[] = [];
      const perfLabels = new Map(PERFORMED_ITEMS.map((p) => [t(p.key), p.key]));
      for (const item of record.performed_items ?? []) {
        const key = perfLabels.get(item);
        if (key) perfMap[key] = true;
        else custom.push(item);
      }
      setPerformed(perfMap);
      const addMap: Record<string, boolean> = {};
      const addLabels = new Map(ADDITIONAL_WORK.map((k) => [t(k), k]));
      for (const item of record.additional_work ?? []) {
        const key = addLabels.get(item);
        if (key) addMap[key] = true;
        else custom.push(item);
      }
      setAdditionalWork(addMap);
      setCustomItems(custom);
      setOilName(record.oil_name ?? '');
      setNextOilKm(record.next_oil_change_km != null ? String(record.next_oil_change_km) : '');
      setServiceByIndicator(!!record.next_service_by_indicator);
      setNextServiceDate(record.next_service_date ?? '');
      setNextServiceKm(record.next_service_km != null ? String(record.next_service_km) : '');
      setNextAdditionalDesc(record.next_additional_desc ?? '');
      setNextAdditionalDate(record.next_additional_date ?? '');
      setNextAdditionalKm(record.next_additional_km != null ? String(record.next_additional_km) : '');
      setDefect(record.defect_found === true ? 'yes' : record.defect_found === false ? 'no' : null);
      setDefectDescription(record.defect_description ?? '');
      setCreateReminder(!!record.create_reminder);
      setShop(record.shop ?? '');
      setWarrantyUntil(record.warranty_until ?? '');
      setTireAction(record.tire_action ?? 'seasonalChange');
      setSeason(record.season ?? 'winter');
    } else {
      resetAll();
    }
    setErr(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, record]);

  function toggle(setter: typeof setPerformed, key: string) {
    setter((s) => ({ ...s, [key]: !s[key] }));
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
      const performedLabels = PERFORMED_ITEMS.filter((p) => performed[p.key]).map((p) => t(p.key));
      const additionalLabels = ADDITIONAL_WORK.filter((k) => additionalWork[k]).map((k) => t(k));
      base.performed_items = performedLabels;
      base.additional_work = [...additionalLabels, ...customItems.filter(Boolean)];
      base.oil_name = oilName || null;
      base.next_oil_change_km = nextOilKm ? Number(nextOilKm) : null;
      base.next_service_by_indicator = serviceByIndicator;
      base.next_service_date = nextServiceDate || null;
      base.next_service_km = nextServiceKm ? Number(nextServiceKm) : null;
      base.next_additional_desc = nextAdditionalDesc || null;
      base.next_additional_date = nextAdditionalDate || null;
      base.next_additional_km = nextAdditionalKm ? Number(nextAdditionalKm) : null;
      base.defect_found = defect === null ? null : defect === 'yes';
      base.defect_description = defect === 'yes' ? defectDescription || null : null;
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
      if (editing && record) {
        await servicesApi.update(record.id, buildBody());
        pushToast(t('common.saved'), 'success');
      } else {
        await servicesApi.create(carId, buildBody());
        pushToast(t('common.created'), 'success');
      }
      onSaved();
    } catch (e2) {
      setErr(apiErrorMessage(e2));
    } finally {
      setSubmitting(false);
    }
  }

  const wide = category === 'service';

  const descPlaceholder =
    category === 'service'
      ? t('service.placeholderService')
      : category === 'repair'
        ? t('service.placeholderRepair')
        : category === 'tires'
          ? t('service.placeholderTires')
          : t('service.placeholderOther');

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={editing ? t('service.editTitle') : t('service.modalTitle')}
      maxWidth={wide ? 720 : 520}
    >
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
            {CATEGORY_CHIPS.map((chip) => {
              const isActive = category === chip.key;
              return (
                <button
                  key={chip.key}
                  type="button"
                  onClick={() => setCategory(chip.key)}
                  className={cn(
                    'rounded-md border px-4 py-2 text-[13px] font-medium transition',
                    isActive
                      ? cn(chip.active, chip.bg)
                      : 'border-border bg-surface text-text-muted hover:bg-bg',
                  )}
                >
                  {t(chip.labelKey)}
                </button>
              );
            })}
          </div>
        </FormField>

        <FormField label={t('service.fieldDescription')}>
          <Input value={description} onChange={(e) => setDescription(e.target.value)} placeholder={descPlaceholder} />
        </FormField>

        <FormField label={t('service.fieldCost')}>
          <Input type="number" step="0.01" value={cost} onChange={(e) => setCost(e.target.value)} />
        </FormField>

        {/* ── Servis extended panel (service-book) ── */}
        {category === 'service' && (
          <div className="rounded-xl border border-border bg-bg/60 p-4">
            <div className="text-sm font-semibold text-text">{t('service.confirmationTitle')}</div>
            <div className="mb-4 text-xs text-text-muted">{t('service.confirmationSubtitle')}</div>

            {/* Performed + Additional side by side */}
            <div className="mb-4 grid grid-cols-1 gap-4 md:grid-cols-2">
              <div>
                <div className="mb-2 border-b border-border pb-1.5 text-[13px] font-bold text-text">
                  {t('service.performedHeader')}
                </div>
                <div className="rounded-lg border border-border bg-surface px-3.5 py-1">
                  {PERFORMED_ITEMS.map((it) => (
                    <CheckItem
                      key={it.key}
                      label={t(it.key)}
                      emphasis={it.emphasis}
                      checked={!!performed[it.key]}
                      onChange={() => toggle(setPerformed, it.key)}
                    />
                  ))}
                </div>
              </div>

              <div>
                <div className="mb-2 border-b border-border pb-1.5 text-[13px] font-bold text-text">
                  {t('service.additionalWork')}
                </div>
                <div className="rounded-lg border border-border bg-surface px-3.5 py-1">
                  {ADDITIONAL_WORK.map((key) => (
                    <CheckItem
                      key={key}
                      label={t(key)}
                      checked={!!additionalWork[key]}
                      onChange={() => toggle(setAdditionalWork, key)}
                    />
                  ))}
                  {customItems.map((item, i) => (
                    <div key={i} className="flex items-center gap-2 py-1.5">
                      <Input
                        value={item}
                        placeholder={t('service.customItemPlaceholder')}
                        onChange={(e) =>
                          setCustomItems((arr) => arr.map((v, j) => (j === i ? e.target.value : v)))
                        }
                      />
                      <button
                        type="button"
                        title={t('common.delete')}
                        aria-label={t('common.delete')}
                        className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-state-red/30 bg-state-red-bg text-state-red"
                        onClick={() => setCustomItems((arr) => arr.filter((_, j) => j !== i))}
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                  <button
                    type="button"
                    className="my-2 inline-flex items-center gap-1.5 rounded-md border border-dashed border-border px-3 py-1.5 text-xs font-semibold text-primary"
                    onClick={() => setCustomItems((arr) => [...arr, ''])}
                  >
                    {t('service.addItem')}
                  </button>
                </div>
              </div>
            </div>

            {/* Oil */}
            <div className="mb-4 grid grid-cols-1 gap-3 md:grid-cols-2">
              <FormField label={t('service.oilName')}>
                <Input value={oilName} onChange={(e) => setOilName(e.target.value)} />
              </FormField>
              <FormField label={t('service.nextOilChange')}>
                <Input type="number" value={nextOilKm} onChange={(e) => setNextOilKm(e.target.value)} />
              </FormField>
            </div>

            {/* Further service dates — two bordered boxes */}
            <div className="mb-2 border-b border-border pb-1.5 text-[13px] font-bold text-text">
              {t('service.furtherTerms')}
            </div>
            <div className="mb-4 flex flex-col gap-3">
              <div className="rounded-lg border border-border bg-surface p-3.5">
                <div className="mb-2.5 text-[13px] font-semibold text-text">{t('service.serviceInspection')}</div>
                <label className="flex cursor-pointer items-center gap-2 text-[13px] text-text">
                  <input
                    type="checkbox"
                    checked={serviceByIndicator}
                    onChange={(e) => setServiceByIndicator(e.target.checked)}
                    className="h-4 w-4 rounded border-[#d1d5db] text-primary focus:ring-primary/30"
                  />
                  {t('service.byIndicator')}
                </label>
                <div className="mb-1.5 mt-2.5 text-[11px] font-semibold text-text-faint">{t('service.orEnterTerm')}</div>
                <div className="grid grid-cols-2 gap-3">
                  <FormField label={t('service.termDay')}>
                    <Input type="date" value={nextServiceDate} onChange={(e) => setNextServiceDate(e.target.value)} />
                  </FormField>
                  <FormField label={t('service.termAt')}>
                    <Input type="number" value={nextServiceKm} onChange={(e) => setNextServiceKm(e.target.value)} />
                  </FormField>
                </div>
              </div>

              <div className="rounded-lg border border-border bg-surface p-3.5">
                <div className="mb-2.5 text-[13px] font-semibold text-text">{t('service.additionalTerm')}</div>
                <FormField label={t('common.description')}>
                  <Input
                    value={nextAdditionalDesc}
                    onChange={(e) => setNextAdditionalDesc(e.target.value)}
                    placeholder={t('service.additionalDescPlaceholder')}
                  />
                </FormField>
                <div className="mb-1.5 mt-2.5 text-[11px] font-semibold text-text-faint">{t('service.orEnterTerm')}</div>
                <div className="grid grid-cols-2 gap-3">
                  <FormField label={t('service.termDay')}>
                    <Input type="date" value={nextAdditionalDate} onChange={(e) => setNextAdditionalDate(e.target.value)} />
                  </FormField>
                  <FormField label={t('service.termAt')}>
                    <Input type="number" value={nextAdditionalKm} onChange={(e) => setNextAdditionalKm(e.target.value)} />
                  </FormField>
                </div>
              </div>
            </div>

            {/* Body inspection — Áno/Nie toggle buttons */}
            <div className="mb-2 border-b border-border pb-1.5 text-[13px] font-bold text-text">
              {t('service.bodyCheck')}
            </div>
            <div className="rounded-lg border border-border bg-surface p-3.5">
              <div className="flex items-center gap-3">
                <span className="text-[13px] font-semibold text-text">{t('service.defectFound')}</span>
                <div className="flex gap-1.5">
                  {(['yes', 'no'] as const).map((v) => {
                    const active = defect === v;
                    const isYes = v === 'yes';
                    return (
                      <button
                        key={v}
                        type="button"
                        onClick={() => setDefect(active ? null : v)}
                        className={cn(
                          'min-w-[50px] rounded-md border px-3 py-1.5 text-xs font-semibold transition',
                          active
                            ? isYes
                              ? 'border-state-red bg-state-red-bg text-state-red'
                              : 'border-state-green bg-state-green-bg text-state-green'
                            : 'border-border bg-surface text-text-faint',
                        )}
                      >
                        {isYes ? t('common.yes') : t('common.no')}
                      </button>
                    );
                  })}
                </div>
              </div>
              {defect === 'yes' && (
                <FormField className="mt-3" label={t('service.defectDescription')}>
                  <Textarea value={defectDescription} onChange={(e) => setDefectDescription(e.target.value)} rows={3} />
                </FormField>
              )}
            </div>

            <label className="mt-3.5 flex cursor-pointer items-center gap-2 text-[13px] text-text">
              <input
                type="checkbox"
                checked={createReminder}
                onChange={(e) => setCreateReminder(e.target.checked)}
                className="h-4 w-4 rounded border-[#d1d5db] text-primary focus:ring-primary/30"
              />
              {t('service.createReminder')}
            </label>
          </div>
        )}

        {/* ── Repair panel ── */}
        {category === 'repair' && (
          <div className="rounded-xl border border-state-orange/30 bg-state-orange-bg/40 p-4">
            <div className="mb-3 text-sm font-semibold text-state-orange">{t('service.repairDetail')}</div>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <FormField label={t('service.repairShop')}>
                <Input value={shop} onChange={(e) => setShop(e.target.value)} />
              </FormField>
              <FormField label={t('service.warrantyUntil')}>
                <Input type="date" value={warrantyUntil} onChange={(e) => setWarrantyUntil(e.target.value)} />
              </FormField>
            </div>
            <FormField className="mt-3" label={t('service.partsList')}>
              <Textarea value={partsList} onChange={(e) => setPartsList(e.target.value)} rows={3} />
            </FormField>
          </div>
        )}

        {/* ── Tires panel ── */}
        {category === 'tires' && (
          <div className="rounded-xl border border-state-green/30 bg-state-green-bg/40 p-4">
            <div className="mb-3 text-sm font-semibold text-state-green">{t('service.tireDetail')}</div>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <FormField label={t('service.tireAction')}>
                <Select value={tireAction} onChange={(e) => setTireAction(e.target.value)}>
                  {TIRE_ACTIONS.map((a) => (
                    <option key={a} value={a}>
                      {t(`service.tireAction_${a}`)}
                    </option>
                  ))}
                </Select>
              </FormField>
              <FormField label={t('service.tireSeason')}>
                <Select value={season} onChange={(e) => setSeason(e.target.value)}>
                  <option value="winter">{t('tires.seasonWinter')}</option>
                  <option value="summer">{t('tires.seasonSummer')}</option>
                  <option value="all_season">{t('tires.seasonAllseason')}</option>
                </Select>
              </FormField>
            </div>
          </div>
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

export default ServiceRecordModal;

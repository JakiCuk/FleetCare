import { useState, type FormEvent } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { carsApi } from '@/api/cars';
import { apiErrorMessage } from '@/api/client';
import { useApi } from '@/hooks/useApi';
import { useUiStore } from '@/stores/uiStore';
import {
  Btn,
  ErrorState,
  FormField,
  Input,
  LoadingState,
  Modal,
  PageHeader,
  Tabs,
} from '@/components/common';
import type { TabItem } from '@/components/common';
import { formatKm } from '@/lib/format';
import type { UpdateCarRequest } from '@/types';
import { OverviewTab } from './car/OverviewTab';
import { DocumentsTab } from './car/DocumentsTab';
import { TiresTab } from './car/TiresTab';
import { ServiceTab } from './car/ServiceTab';
import { FuelTab } from './car/FuelTab';
import { CostsTab } from './car/CostsTab';

type TabKey = 'overview' | 'documents' | 'tires' | 'service' | 'fuel' | 'costs';

export default function CarDetailPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const pushToast = useUiStore((s) => s.pushToast);
  const params = useParams();
  const carId = Number(params.id);

  const { data: car, loading, error, reload } = useApi(() => carsApi.get(carId), [carId]);
  const [tab, setTab] = useState<TabKey>('overview');
  const [editOpen, setEditOpen] = useState(false);

  const tabs: TabItem[] = [
    { key: 'overview', label: t('car.tabOverview') },
    { key: 'documents', label: t('car.tabDocuments') },
    { key: 'tires', label: t('car.tabTires') },
    { key: 'service', label: t('car.tabService') },
    { key: 'fuel', label: t('car.tabFuel') },
    { key: 'costs', label: t('car.tabCosts') },
  ];

  async function deleteCar() {
    if (!window.confirm(t('car.deleteConfirm'))) return;
    try {
      await carsApi.remove(carId);
      pushToast(t('common.deleted'), 'success');
      navigate('/cars');
    } catch (err) {
      pushToast(apiErrorMessage(err), 'error');
    }
  }

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={reload} />;
  if (!car) return null;

  return (
    <div>
      <PageHeader
        breadcrumb={
          <span>
            <Link to="/" className="hover:text-text">
              {t('car.breadcrumbDashboard')}
            </Link>
            {' / '}
            <Link to="/cars" className="hover:text-text">
              {t('car.breadcrumbVehicles')}
            </Link>
            {' / '}
            <span className="text-text">{car.full_name}</span>
          </span>
        }
        title={car.full_name}
        subtitle={
          <span className="font-mono text-xs">
            {car.license_plate} · {car.vin} · {car.year} · {formatKm(car.current_odometer_km)}
          </span>
        }
        actions={
          <>
            <Btn variant="secondary" onClick={() => setEditOpen(true)}>
              {t('car.edit')}
            </Btn>
            <Btn variant="danger" onClick={deleteCar}>
              {t('car.delete')}
            </Btn>
          </>
        }
      />

      <Tabs items={tabs} active={tab} onChange={(k) => setTab(k as TabKey)} className="mb-5" />

      {tab === 'overview' && <OverviewTab car={car} onChanged={reload} />}
      {tab === 'documents' && <DocumentsTab carId={car.id} />}
      {tab === 'tires' && <TiresTab carId={car.id} currentOdometer={car.current_odometer_km} />}
      {tab === 'service' && <ServiceTab carId={car.id} currentOdometer={car.current_odometer_km} />}
      {tab === 'fuel' && <FuelTab carId={car.id} currentOdometer={car.current_odometer_km} />}
      {tab === 'costs' && <CostsTab carId={car.id} />}

      {editOpen && (
        <EditCarModal
          open={editOpen}
          car={car}
          onClose={() => setEditOpen(false)}
          onSaved={() => {
            setEditOpen(false);
            reload();
          }}
        />
      )}
    </div>
  );
}

function EditCarModal({
  open,
  car,
  onClose,
  onSaved,
}: {
  open: boolean;
  car: { id: number; name: string; make: string; model: string; year: number; license_plate: string; vin: string; current_odometer_km: number };
  onClose: () => void;
  onSaved: () => void;
}) {
  const { t } = useTranslation();
  const pushToast = useUiStore((s) => s.pushToast);
  const [form, setForm] = useState<UpdateCarRequest>({
    name: car.name,
    make: car.make,
    model: car.model,
    year: car.year,
    license_plate: car.license_plate,
    vin: car.vin,
    current_odometer_km: car.current_odometer_km,
  });
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  function set<K extends keyof UpdateCarRequest>(key: K, value: UpdateCarRequest[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setErr(null);
    try {
      await carsApi.update(car.id, form);
      pushToast(t('common.saved'), 'success');
      onSaved();
    } catch (e2) {
      setErr(apiErrorMessage(e2));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={t('car.editTitle')} maxWidth={520}>
      <form onSubmit={submit} className="flex flex-col gap-4">
        <FormField label={t('addCar.name')} required>
          <Input value={form.name ?? ''} onChange={(e) => set('name', e.target.value)} required />
        </FormField>
        <div className="grid grid-cols-2 gap-3">
          <FormField label={t('addCar.make')}>
            <Input value={form.make ?? ''} onChange={(e) => set('make', e.target.value)} />
          </FormField>
          <FormField label={t('addCar.model')}>
            <Input value={form.model ?? ''} onChange={(e) => set('model', e.target.value)} />
          </FormField>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <FormField label={t('addCar.year')}>
            <Input type="number" value={form.year ?? ''} onChange={(e) => set('year', Number(e.target.value))} />
          </FormField>
          <FormField label={t('addCar.licensePlate')}>
            <Input className="font-mono" value={form.license_plate ?? ''} onChange={(e) => set('license_plate', e.target.value)} />
          </FormField>
        </div>
        <FormField label={t('addCar.vin')}>
          <Input className="font-mono" value={form.vin ?? ''} onChange={(e) => set('vin', e.target.value)} />
        </FormField>
        <FormField label={t('addCar.odometer')}>
          <Input
            type="number"
            value={form.current_odometer_km ?? ''}
            onChange={(e) => set('current_odometer_km', Number(e.target.value))}
          />
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

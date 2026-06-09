import { useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { carsApi } from '@/api/cars';
import { useApi } from '@/hooks/useApi';
import {
  Badge,
  Btn,
  Card,
  Column,
  ErrorState,
  Input,
  LoadingState,
  OverdueBadge,
  PageHeader,
  StatusChip,
  Table,
} from '@/components/common';
import { AddCarModal } from './dashboard/AddCarModal';
import { formatKm } from '@/lib/format';
import type { CarListItem } from '@/types';

export default function CarsListPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { data, loading, error, reload } = useApi(() => carsApi.list(), []);
  const [query, setQuery] = useState('');
  const [addOpen, setAddOpen] = useState(false);

  const filtered = useMemo(() => {
    const cars = data ?? [];
    const q = query.trim().toLowerCase();
    if (!q) return cars;
    return cars.filter(
      (c) =>
        c.full_name.toLowerCase().includes(q) ||
        c.name.toLowerCase().includes(q) ||
        c.license_plate.toLowerCase().includes(q) ||
        c.vin.toLowerCase().includes(q),
    );
  }, [data, query]);

  const columns: Column<CarListItem>[] = [
    { key: 'car', header: t('cars.colCar'), render: (c) => <span className="font-medium">{c.full_name}</span> },
    { key: 'plate', header: t('cars.colPlate'), render: (c) => <span className="font-mono text-xs">{c.license_plate}</span> },
    {
      key: 'vin',
      header: t('cars.colVin'),
      render: (c) => (
        <span className="font-mono text-xs text-text-muted">{c.vin ? `${c.vin.slice(0, 8)}…` : '—'}</span>
      ),
    },
    { key: 'year', header: t('cars.colYear'), render: (c) => c.year },
    { key: 'odometer', header: t('cars.colOdometer'), align: 'right', render: (c) => formatKm(c.current_odometer_km) },
    {
      key: 'stk',
      header: t('cars.colStk'),
      render: (c) =>
        c.stk ? <StatusChip label="STK" days={c.stk.days_left} urgentThreshold={14} /> : <span className="text-text-faint">–</span>,
    },
    {
      key: 'insurance',
      header: t('cars.colInsurance'),
      render: (c) => (
        <span className="flex flex-wrap gap-1">
          {c.pzp && <StatusChip label="PZP" days={c.pzp.days_left} urgentThreshold={14} />}
          {c.kasko && <StatusChip label="KASKO" days={c.kasko.days_left} urgentThreshold={14} />}
          {!c.pzp && !c.kasko && <span className="text-text-faint">–</span>}
        </span>
      ),
    },
    {
      key: 'status',
      header: t('cars.colStatus'),
      render: (c) => (c.overdue ? <OverdueBadge /> : <Badge variant="green">{t('cars.statusOk')}</Badge>),
    },
    {
      key: 'detail',
      header: t('cars.colDetail'),
      align: 'right',
      render: (c) => (
        <Link to={`/cars/${c.id}`} className="text-primary hover:underline" onClick={(e) => e.stopPropagation()}>
          {t('common.detail')} →
        </Link>
      ),
    },
  ];

  return (
    <div>
      <PageHeader
        title={t('cars.title')}
        subtitle={t('cars.subtitle')}
        actions={<Btn onClick={() => setAddOpen(true)}>{t('dashboard.addCar')}</Btn>}
      />

      <div className="mb-4 max-w-sm">
        <Input
          placeholder={t('cars.searchPlaceholder')}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>

      {loading && <LoadingState />}
      {error && <ErrorState message={error} onRetry={reload} />}

      {data && (
        <Card padded={false} className="p-2">
          <Table
            columns={columns}
            rows={filtered}
            rowKey={(c) => c.id}
            emptyMsg={t('cars.empty')}
            onRowClick={(c) => navigate(`/cars/${c.id}`)}
          />
        </Card>
      )}

      <AddCarModal
        open={addOpen}
        onClose={() => setAddOpen(false)}
        onCreated={(car) => navigate(`/cars/${car.id}`)}
      />
    </div>
  );
}

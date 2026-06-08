import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { dashboardApi } from '@/api/dashboard';
import { useApi } from '@/hooks/useApi';
import { Btn, EmptyState, ErrorState, LoadingState, PageHeader, StatCard } from '@/components/common';
import { formatMoney } from '@/lib/format';
import { CarCard } from './dashboard/CarCard';
import { AddCarModal } from './dashboard/AddCarModal';

export default function DashboardPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { data, loading, error, reload } = useApi(() => dashboardApi.get(), []);
  const [addOpen, setAddOpen] = useState(false);

  return (
    <div>
      <PageHeader
        title={t('dashboard.title')}
        subtitle={t('dashboard.subtitle')}
        actions={<Btn onClick={() => setAddOpen(true)}>{t('dashboard.addCar')}</Btn>}
      />

      {loading && <LoadingState />}
      {error && <ErrorState message={error} onRetry={reload} />}

      {data && (
        <>
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <StatCard label={t('dashboard.statCars')} value={data.stats.cars} color="blue" />
            <StatCard
              label={t('dashboard.statNotifications')}
              value={data.stats.notifications_today}
              color="amber"
            />
            <StatCard
              label={t('dashboard.statOverdue')}
              value={data.stats.overdue_items}
              color="red"
            />
            <StatCard
              label={t('dashboard.statMonthlyCost')}
              value={formatMoney(data.stats.monthly_cost)}
              color="green"
            />
          </div>

          <h2 className="mb-3 mt-8 text-base font-semibold text-text">
            {t('dashboard.vehicles')}
          </h2>

          {data.cars.length === 0 ? (
            <EmptyState
              icon="🚗"
              title={t('dashboard.emptyTitle')}
              subtitle={t('dashboard.emptySubtitle')}
              action={<Btn onClick={() => setAddOpen(true)}>{t('dashboard.addCar')}</Btn>}
            />
          ) : (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
              {data.cars.map((car) => (
                <CarCard key={car.id} car={car} />
              ))}
            </div>
          )}
        </>
      )}

      <AddCarModal
        open={addOpen}
        onClose={() => setAddOpen(false)}
        onCreated={(car) => navigate(`/cars/${car.id}`)}
      />
    </div>
  );
}

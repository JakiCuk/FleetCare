import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import type { DashboardCar } from '@/types';
import { StatusChip, OverdueBadge } from '@/components/common';
import { formatKm } from '@/lib/format';
import { cn } from '@/lib/cn';

interface CarCardProps {
  car: DashboardCar;
}

/** Dashboard vehicle card (DESIGN_SYSTEM §5: red rail + OVERDUE when overdue). */
export function CarCard({ car }: CarCardProps) {
  const { t } = useTranslation();

  return (
    <Link
      to={`/cars/${car.id}`}
      className={cn(
        'flex flex-col gap-3 rounded-card border bg-surface p-5 shadow-card transition hover:shadow-md',
        car.overdue ? 'border-2 border-state-red' : 'border-border',
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <div className="font-semibold text-text">{car.name}</div>
          <div className="text-xs text-text-muted">{formatKm(car.current_odometer_km)}</div>
        </div>
        {car.overdue && <OverdueBadge />}
      </div>

      <div className="font-mono text-xs text-text-faint">{car.license_plate}</div>

      {car.chips.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {car.chips.map((chip, i) => (
            <StatusChip key={`${chip.label}-${i}`} label={chip.label} days={chip.days_left} />
          ))}
        </div>
      )}

      <div className="mt-1 grid grid-cols-2 gap-3 border-t border-border-soft pt-3">
        <div>
          <div className="text-[11px] uppercase tracking-wide text-text-faint">
            {t('dashboard.nextService')}
          </div>
          <div className="text-[13px] text-text">{car.next_service ?? '—'}</div>
        </div>
        <div>
          <div className="text-[11px] uppercase tracking-wide text-text-faint">
            {t('dashboard.tires')}
          </div>
          <div className="text-[13px] text-text">{car.tires ?? '—'}</div>
        </div>
      </div>

      <div className="mt-1 text-[13px] font-medium text-primary">{t('common.openDetail')}</div>
    </Link>
  );
}

export default CarCard;

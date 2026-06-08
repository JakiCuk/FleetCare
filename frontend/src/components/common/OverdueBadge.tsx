import { useTranslation } from 'react-i18next';
import { cn } from '@/lib/cn';

interface OverdueBadgeProps {
  className?: string;
}

/** Solid red OVERDUE badge, 11/700, letter-spaced (DESIGN_SYSTEM §4). */
export function OverdueBadge({ className }: OverdueBadgeProps) {
  const { t } = useTranslation();
  return (
    <span
      className={cn(
        'inline-flex items-center rounded bg-state-red px-2 py-0.5 text-[11px] font-bold tracking-wider text-white',
        className,
      )}
    >
      {t('common.overdue')}
    </span>
  );
}

export default OverdueBadge;

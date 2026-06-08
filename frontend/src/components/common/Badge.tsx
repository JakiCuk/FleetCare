import type { ReactNode } from 'react';
import type { ChipVariant } from '@/types';
import { variantClasses } from '@/lib/colors';
import { cn } from '@/lib/cn';

interface BadgeProps {
  variant?: ChipVariant;
  children: ReactNode;
  className?: string;
}

export function Badge({ variant = 'gray', children, className }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded px-2 py-0.5 text-xs font-semibold',
        variantClasses[variant],
        className,
      )}
    >
      {children}
    </span>
  );
}

export default Badge;

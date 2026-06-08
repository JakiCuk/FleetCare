import type { ReactNode } from 'react';
import { cn } from '@/lib/cn';

interface CardProps {
  children: ReactNode;
  className?: string;
  /** Optional title rendered as a 14/600 header inside the card. */
  title?: ReactNode;
  actions?: ReactNode;
  padded?: boolean;
}

export function Card({ children, className, title, actions, padded = true }: CardProps) {
  return (
    <div
      className={cn(
        'rounded-card border border-border bg-surface shadow-card',
        padded && 'p-5',
        className,
      )}
    >
      {(title || actions) && (
        <div className="mb-4 flex items-center justify-between gap-2">
          {title && <h3 className="text-sm font-semibold text-text">{title}</h3>}
          {actions && <div className="flex items-center gap-2">{actions}</div>}
        </div>
      )}
      {children}
    </div>
  );
}

export default Card;

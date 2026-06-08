import type { ButtonHTMLAttributes, ReactNode } from 'react';
import { cn } from '@/lib/cn';

export type BtnVariant = 'primary' | 'secondary' | 'danger' | 'ghost';
export type BtnSize = 'sm' | 'md';

interface BtnProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: BtnVariant;
  size?: BtnSize;
  children: ReactNode;
}

const variantClasses: Record<BtnVariant, string> = {
  primary: 'bg-primary text-white hover:opacity-85 border border-primary',
  secondary: 'bg-surface text-text border border-border hover:bg-bg',
  danger: 'bg-state-red-bg text-state-red border border-state-red-bg hover:opacity-85',
  ghost: 'bg-transparent text-text-muted border border-transparent hover:bg-bg',
};

const sizeClasses: Record<BtnSize, string> = {
  sm: 'text-xs px-3 py-1.5',
  md: 'text-[13px] px-4 py-2',
};

export function Btn({
  variant = 'primary',
  size = 'md',
  className,
  children,
  type = 'button',
  ...rest
}: BtnProps) {
  return (
    <button
      type={type}
      className={cn(
        'inline-flex items-center justify-center gap-1.5 rounded-md font-medium transition disabled:opacity-50 disabled:cursor-not-allowed',
        variantClasses[variant],
        sizeClasses[size],
        className,
      )}
      {...rest}
    >
      {children}
    </button>
  );
}

export default Btn;

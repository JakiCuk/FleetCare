import type { ReactNode } from 'react';

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  subtitle?: string;
  action?: ReactNode;
}

export function EmptyState({ icon = '📭', title, subtitle, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 px-4 py-12 text-center">
      <div className="text-3xl opacity-70">{icon}</div>
      <div className="text-sm font-semibold text-text">{title}</div>
      {subtitle && <div className="max-w-sm text-sm text-text-muted">{subtitle}</div>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}

export default EmptyState;

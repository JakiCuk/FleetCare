import { cn } from '@/lib/cn';

export type StatColor = 'blue' | 'amber' | 'red' | 'green' | 'gray';

interface StatCardProps {
  label: string;
  value: string | number;
  color?: StatColor;
  hint?: string;
}

const valueColor: Record<StatColor, string> = {
  blue: 'text-primary',
  amber: 'text-state-yellow',
  red: 'text-state-red',
  green: 'text-state-green',
  gray: 'text-text',
};

export function StatCard({ label, value, color = 'gray', hint }: StatCardProps) {
  return (
    <div className="rounded-card border border-border bg-surface p-5 shadow-card">
      <div className="text-xs font-medium uppercase tracking-wide text-text-muted">
        {label}
      </div>
      <div className={cn('mt-1 text-[28px] font-bold leading-tight', valueColor[color])}>
        {value}
      </div>
      {hint && <div className="mt-1 text-xs text-text-faint">{hint}</div>}
    </div>
  );
}

export default StatCard;

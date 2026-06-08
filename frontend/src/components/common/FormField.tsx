import type { ReactNode } from 'react';
import { cn } from '@/lib/cn';

interface FormFieldProps {
  label?: ReactNode;
  htmlFor?: string;
  error?: string | null;
  hint?: string;
  required?: boolean;
  children: ReactNode;
  className?: string;
}

export function FormField({
  label,
  htmlFor,
  error,
  hint,
  required,
  children,
  className,
}: FormFieldProps) {
  return (
    <div className={cn('flex flex-col gap-1', className)}>
      {label && (
        <label htmlFor={htmlFor} className="text-[13px] font-medium text-text">
          {label}
          {required && <span className="ml-0.5 text-state-red">*</span>}
        </label>
      )}
      {children}
      {hint && !error && <span className="text-xs text-text-faint">{hint}</span>}
      {error && <span className="text-xs text-state-red">{error}</span>}
    </div>
  );
}

export default FormField;

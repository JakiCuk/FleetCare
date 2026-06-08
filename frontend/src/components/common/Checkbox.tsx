import type { InputHTMLAttributes, ReactNode } from 'react';
import { cn } from '@/lib/cn';

interface CheckboxProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label?: ReactNode;
}

export function Checkbox({ label, className, id, ...rest }: CheckboxProps) {
  return (
    <label
      htmlFor={id}
      className={cn('inline-flex cursor-pointer items-center gap-2 text-[13px] text-text', className)}
    >
      <input
        id={id}
        type="checkbox"
        className="h-4 w-4 rounded border-[#d1d5db] text-primary focus:ring-primary/30"
        {...rest}
      />
      {label && <span>{label}</span>}
    </label>
  );
}

export default Checkbox;

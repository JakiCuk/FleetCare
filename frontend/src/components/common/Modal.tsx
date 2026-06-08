import { useEffect } from 'react';
import type { ReactNode } from 'react';
import { cn } from '@/lib/cn';

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title?: ReactNode;
  children: ReactNode;
  /** Max width in px (default 480). */
  maxWidth?: number;
  footer?: ReactNode;
}

export function Modal({ open, onClose, title, children, maxWidth = 480, footer }: ModalProps) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/40 p-4 py-10"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        className="w-full rounded-xl bg-surface p-7 shadow-modal"
        style={{ maxWidth }}
        role="dialog"
        aria-modal="true"
      >
        <div className="mb-5 flex items-start justify-between gap-4">
          {title && <h2 className="text-lg font-bold text-text">{title}</h2>}
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className={cn(
              'ml-auto -mr-2 -mt-2 flex h-8 w-8 items-center justify-center rounded-md text-text-muted',
              'hover:bg-bg hover:text-text',
            )}
          >
            ✕
          </button>
        </div>
        {children}
        {footer && <div className="mt-6 flex justify-end gap-2">{footer}</div>}
      </div>
    </div>
  );
}

export default Modal;

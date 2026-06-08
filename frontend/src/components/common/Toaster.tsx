import { useUiStore } from '@/stores/uiStore';
import { cn } from '@/lib/cn';

const variantClasses = {
  success: 'border-state-green/30 bg-state-green-bg text-state-green',
  error: 'border-state-red/30 bg-state-red-bg text-state-red',
  info: 'border-border bg-surface text-text',
};

export function Toaster() {
  const toasts = useUiStore((s) => s.toasts);
  const dismiss = useUiStore((s) => s.dismissToast);

  if (toasts.length === 0) return null;

  return (
    <div className="pointer-events-none fixed bottom-4 right-4 z-[60] flex w-80 max-w-[calc(100vw-2rem)] flex-col gap-2">
      {toasts.map((toast) => (
        <button
          key={toast.id}
          type="button"
          onClick={() => dismiss(toast.id)}
          className={cn(
            'pointer-events-auto rounded-lg border px-4 py-3 text-left text-[13px] font-medium shadow-card transition',
            variantClasses[toast.variant],
          )}
        >
          {toast.message}
        </button>
      ))}
    </div>
  );
}

export default Toaster;

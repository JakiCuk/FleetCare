import { useTranslation } from 'react-i18next';
import { Btn } from './Btn';

export function Spinner({ className }: { className?: string }) {
  return (
    <span
      className={`inline-block h-5 w-5 animate-spin rounded-full border-2 border-border border-t-primary ${className ?? ''}`}
      role="status"
      aria-label="loading"
    />
  );
}

export function LoadingState({ label }: { label?: string }) {
  const { t } = useTranslation();
  return (
    <div className="flex items-center justify-center gap-2 px-4 py-12 text-sm text-text-muted">
      <Spinner />
      <span>{label ?? t('common.loading')}</span>
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  const { t } = useTranslation();
  return (
    <div className="flex flex-col items-center justify-center gap-3 px-4 py-12 text-center">
      <div className="text-3xl">⚠️</div>
      <div className="text-sm font-semibold text-state-red">{t('common.error')}</div>
      <div className="max-w-md text-sm text-text-muted">{message}</div>
      {onRetry && (
        <Btn variant="secondary" size="sm" onClick={onRetry}>
          {t('common.retry')}
        </Btn>
      )}
    </div>
  );
}

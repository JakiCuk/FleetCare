import { useState, type FormEvent } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuthStore } from '@/stores/authStore';
import { apiErrorMessage } from '@/api/client';
import { Btn, FormField, Input } from '@/components/common';

export default function LoginPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const login = useAuthStore((s) => s.login);
  const user = useAuthStore((s) => s.user);

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (user) return <Navigate to="/" replace />;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await login({ username, password });
      navigate('/', { replace: true });
    } catch (err) {
      setError(apiErrorMessage(err, t('login.error')));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-bg px-4">
      <div className="w-full max-w-sm rounded-card border border-border bg-surface p-7 shadow-card">
        <div className="mb-6 text-center">
          <div className="text-3xl">🚗</div>
          <h1 className="mt-2 text-xl font-bold text-text">{t('common.appName')}</h1>
          <p className="mt-1 text-sm text-text-muted">{t('login.subtitle')}</p>
        </div>

        <form onSubmit={onSubmit} className="flex flex-col gap-4">
          <FormField label={t('login.username')} htmlFor="username">
            <Input
              id="username"
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </FormField>
          <FormField label={t('login.password')} htmlFor="password">
            <Input
              id="password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </FormField>

          {error && <p className="text-sm text-state-red">{error}</p>}

          <Btn type="submit" disabled={submitting} className="w-full">
            {submitting ? t('login.submitting') : t('login.submit')}
          </Btn>
        </form>
      </div>
    </div>
  );
}

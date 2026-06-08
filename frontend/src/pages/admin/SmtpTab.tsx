import { useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { settingsApi } from '@/api/settings';
import { apiErrorMessage } from '@/api/client';
import { useApi } from '@/hooks/useApi';
import { useUiStore } from '@/stores/uiStore';
import {
  Badge,
  Btn,
  Card,
  ErrorState,
  FormField,
  Input,
  LoadingState,
  Select,
} from '@/components/common';
import type { SmtpEncryption } from '@/types';

export function SmtpTab() {
  const { t } = useTranslation();
  const pushToast = useUiStore((s) => s.pushToast);
  const { data, loading, error, reload } = useApi(() => settingsApi.get(), []);

  const [host, setHost] = useState('');
  const [port, setPort] = useState('587');
  const [encryption, setEncryption] = useState<SmtpEncryption>('tls');
  const [username, setUsername] = useState('');
  const [from, setFrom] = useState('');
  const [password, setPassword] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (data) {
      setHost(data.smtp.host ?? '');
      setPort(String(data.smtp.port ?? 587));
      setEncryption(data.smtp.encryption);
      setUsername(data.smtp.username ?? '');
      setFrom(data.smtp.from ?? '');
    }
  }, [data]);

  async function save(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await settingsApi.update({
        smtp: {
          host,
          port: Number(port),
          encryption,
          username,
          from,
          ...(password ? { password } : {}),
        },
      });
      pushToast(t('settings.saved'), 'success');
      setPassword('');
      reload();
    } catch (err) {
      pushToast(apiErrorMessage(err), 'error');
    } finally {
      setSaving(false);
    }
  }

  async function test() {
    try {
      const res = await settingsApi.testSmtp();
      pushToast(`SMTP: ${res.status}`, res.status === 'ok' ? 'success' : 'info');
    } catch (err) {
      pushToast(apiErrorMessage(err), 'error');
    }
  }

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={reload} />;

  return (
    <Card title={t('admin.smtpTitle')}>
      <form onSubmit={save} className="flex flex-col gap-4">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <FormField label={t('admin.smtpHost')}>
            <Input value={host} onChange={(e) => setHost(e.target.value)} />
          </FormField>
          <FormField label={t('admin.smtpPort')}>
            <Input type="number" value={port} onChange={(e) => setPort(e.target.value)} />
          </FormField>
          <FormField label={t('admin.smtpEncryption')}>
            <Select value={encryption} onChange={(e) => setEncryption(e.target.value as SmtpEncryption)}>
              <option value="tls">TLS</option>
              <option value="ssl">SSL</option>
              <option value="none">None</option>
            </Select>
          </FormField>
          <FormField label={t('admin.smtpUsername')}>
            <Input value={username} onChange={(e) => setUsername(e.target.value)} />
          </FormField>
          <FormField label={t('admin.smtpFrom')} className="sm:col-span-2">
            <Input value={from} onChange={(e) => setFrom(e.target.value)} />
          </FormField>
          <FormField
            label={t('admin.smtpPassword')}
            hint={data?.smtp.password_set ? t('admin.smtpPasswordSet') : undefined}
            className="sm:col-span-2"
          >
            <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" />
          </FormField>
        </div>

        <div className="flex items-center gap-2">
          <Btn type="submit" disabled={saving}>
            {saving ? t('common.saving') : t('common.save')}
          </Btn>
          <Btn type="button" variant="secondary" onClick={test}>
            {t('admin.smtpTest')}
          </Btn>
          {data?.smtp.password_set && <Badge variant="green">{t('admin.smtpPasswordSet')}</Badge>}
        </div>
      </form>
    </Card>
  );
}

export default SmtpTab;

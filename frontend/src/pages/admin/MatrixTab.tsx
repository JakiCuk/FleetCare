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
  Checkbox,
  ErrorState,
  FormField,
  Input,
  LoadingState,
} from '@/components/common';

export function MatrixTab() {
  const { t } = useTranslation();
  const pushToast = useUiStore((s) => s.pushToast);
  const { data, loading, error, reload } = useApi(() => settingsApi.get(), []);

  const [enabled, setEnabled] = useState(false);
  const [homeserver, setHomeserver] = useState('');
  const [defaultRoom, setDefaultRoom] = useState('');
  const [token, setToken] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (data) {
      setEnabled(data.matrix.enabled);
      setHomeserver(data.matrix.homeserver ?? '');
      setDefaultRoom(data.matrix.default_room ?? '');
    }
  }, [data]);

  async function save(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await settingsApi.update({
        matrix: {
          enabled,
          homeserver,
          default_room: defaultRoom,
          ...(token ? { token } : {}),
        },
      });
      pushToast(t('settings.saved'), 'success');
      setToken('');
      reload();
    } catch (err) {
      pushToast(apiErrorMessage(err), 'error');
    } finally {
      setSaving(false);
    }
  }

  async function test() {
    try {
      const res = await settingsApi.testMatrix();
      pushToast(`Matrix: ${res.status}`, res.status === 'ok' ? 'success' : 'info');
    } catch (err) {
      pushToast(apiErrorMessage(err), 'error');
    }
  }

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={reload} />;

  return (
    <Card title={t('admin.matrixTitle')}>
      <form onSubmit={save} className="flex flex-col gap-4">
        <Checkbox
          id="matrix-enabled"
          label={t('admin.matrixEnabled')}
          checked={enabled}
          onChange={(e) => setEnabled(e.target.checked)}
        />
        <FormField label={t('admin.matrixHomeserver')}>
          <Input value={homeserver} onChange={(e) => setHomeserver(e.target.value)} />
        </FormField>
        <FormField label={t('admin.matrixRoom')}>
          <Input value={defaultRoom} onChange={(e) => setDefaultRoom(e.target.value)} className="font-mono" />
        </FormField>
        <FormField
          label={t('admin.matrixToken')}
          hint={data?.matrix.token_set ? t('admin.matrixTokenSet') : undefined}
        >
          <Input type="password" value={token} onChange={(e) => setToken(e.target.value)} placeholder="••••••••" />
        </FormField>

        <div className="flex items-center gap-2">
          <Btn type="submit" disabled={saving}>
            {saving ? t('common.saving') : t('common.save')}
          </Btn>
          <Btn type="button" variant="secondary" onClick={test}>
            {t('admin.matrixTest')}
          </Btn>
          {data?.matrix.token_set && <Badge variant="green">{t('admin.matrixTokenSet')}</Badge>}
        </div>
      </form>
    </Card>
  );
}

export default MatrixTab;

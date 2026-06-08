import { useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { settingsApi } from '@/api/settings';
import { usersApi } from '@/api/users';
import { apiErrorMessage } from '@/api/client';
import { useApi } from '@/hooks/useApi';
import { usePwaInstall } from '@/hooks/usePwaInstall';
import { useUiStore } from '@/stores/uiStore';
import { useAuthStore } from '@/stores/authStore';
import {
  Btn,
  Card,
  ErrorState,
  FormField,
  Input,
  LoadingState,
  PageHeader,
  Select,
} from '@/components/common';
import type { Locale, UpdateSettingsRequest } from '@/types';

export default function SettingsPage() {
  const { t } = useTranslation();
  const pushToast = useUiStore((s) => s.pushToast);
  const locale = useUiStore((s) => s.locale);
  const setLocale = useUiStore((s) => s.setLocale);
  const user = useAuthStore((s) => s.user);
  const setUser = useAuthStore((s) => s.setUser);
  const { canInstall, installed, promptInstall } = usePwaInstall();

  const { data, loading, error, reload } = useApi(() => settingsApi.get(), []);
  const isAdmin = Boolean(user?.is_admin);

  const [form, setForm] = useState({
    fleet_name: '',
    timezone: '',
    currency: '',
    daily_send_time: '08:00',
    tire_min_tread_mm: 2.5,
    lead1: 30,
    lead2: 14,
    lead3: 7,
  });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (data) {
      setForm({
        fleet_name: data.fleet_name,
        timezone: data.timezone,
        currency: data.currency,
        daily_send_time: data.daily_send_time,
        tire_min_tread_mm: data.tire_min_tread_mm,
        lead1: data.default_lead_days[1],
        lead2: data.default_lead_days[2],
        lead3: data.default_lead_days[3],
      });
    }
  }, [data]);

  async function changeLanguage(value: Locale) {
    setLocale(value);
    // Persist on the user profile too (best-effort).
    if (user) {
      try {
        const updated = await usersApi.update(user.id, { locale: value });
        setUser(updated);
      } catch {
        // local choice still applies via localStorage
      }
    }
  }

  async function save(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const body: UpdateSettingsRequest = {
        fleet_name: form.fleet_name,
        timezone: form.timezone,
        currency: form.currency,
        daily_send_time: form.daily_send_time,
        tire_min_tread_mm: Number(form.tire_min_tread_mm),
        default_lead_days: { 1: Number(form.lead1), 2: Number(form.lead2), 3: Number(form.lead3) },
      };
      await settingsApi.update(body);
      pushToast(t('settings.saved'), 'success');
      reload();
    } catch (err) {
      pushToast(apiErrorMessage(err), 'error');
    } finally {
      setSaving(false);
    }
  }

  async function wipe() {
    if (!window.confirm(t('settings.wipeConfirm'))) return;
    try {
      await settingsApi.wipe();
      pushToast(t('common.deleted'), 'success');
    } catch (err) {
      pushToast(apiErrorMessage(err), 'error');
    }
  }

  return (
    <div>
      <PageHeader title={t('settings.title')} subtitle={t('settings.subtitle')} />

      {loading && <LoadingState />}
      {error && <ErrorState message={error} onRetry={reload} />}

      <div className="flex flex-col gap-5">
        {/* Language is available to every user even before settings load. */}
        <Card title={t('settings.general')}>
          <form onSubmit={save} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <FormField label={t('settings.fleetName')}>
              <Input
                value={form.fleet_name}
                disabled={!isAdmin}
                onChange={(e) => setForm((f) => ({ ...f, fleet_name: e.target.value }))}
              />
            </FormField>
            <FormField label={t('settings.timezone')}>
              <Input
                value={form.timezone}
                disabled={!isAdmin}
                onChange={(e) => setForm((f) => ({ ...f, timezone: e.target.value }))}
              />
            </FormField>
            <FormField label={t('settings.language')}>
              <Select value={locale} onChange={(e) => changeLanguage(e.target.value as Locale)}>
                <option value="sk">{t('settings.langSk')}</option>
                <option value="en">{t('settings.langEn')}</option>
              </Select>
            </FormField>
            <FormField label={t('settings.currency')}>
              <Input
                value={form.currency}
                disabled={!isAdmin}
                onChange={(e) => setForm((f) => ({ ...f, currency: e.target.value }))}
              />
            </FormField>
            {isAdmin && (
              <div className="sm:col-span-2">
                <Btn type="submit" disabled={saving}>
                  {saving ? t('common.saving') : t('common.save')}
                </Btn>
              </div>
            )}
          </form>
        </Card>

        {isAdmin && (
          <Card title={t('settings.notifications')}>
            <form onSubmit={save} className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <FormField label={t('settings.lead1')}>
                <Input type="number" value={form.lead1} onChange={(e) => setForm((f) => ({ ...f, lead1: Number(e.target.value) }))} />
              </FormField>
              <FormField label={t('settings.lead2')}>
                <Input type="number" value={form.lead2} onChange={(e) => setForm((f) => ({ ...f, lead2: Number(e.target.value) }))} />
              </FormField>
              <FormField label={t('settings.lead3')}>
                <Input type="number" value={form.lead3} onChange={(e) => setForm((f) => ({ ...f, lead3: Number(e.target.value) }))} />
              </FormField>
              <FormField label={t('settings.sendTime')}>
                <Input type="time" value={form.daily_send_time} onChange={(e) => setForm((f) => ({ ...f, daily_send_time: e.target.value }))} />
              </FormField>
              <FormField label={t('settings.minTread')}>
                <Input
                  type="number"
                  step="0.1"
                  value={form.tire_min_tread_mm}
                  onChange={(e) => setForm((f) => ({ ...f, tire_min_tread_mm: Number(e.target.value) }))}
                />
              </FormField>
              <div className="sm:col-span-3">
                <Btn type="submit" disabled={saving}>
                  {saving ? t('common.saving') : t('common.save')}
                </Btn>
              </div>
            </form>
          </Card>
        )}

        <Card title={t('settings.pwa')}>
          <p className="mb-3 text-sm text-text-muted">{t('settings.pwaDescription')}</p>
          {installed ? (
            <p className="text-sm font-medium text-state-green">{t('settings.pwaInstalled')}</p>
          ) : canInstall ? (
            <Btn onClick={promptInstall}>{t('settings.pwaInstall')}</Btn>
          ) : (
            <p className="text-sm text-text-faint">{t('settings.pwaUnavailable')}</p>
          )}
        </Card>

        {isAdmin && (
          <Card title={t('settings.dangerZone')} className="border-state-red/30">
            <div className="flex flex-wrap gap-2">
              <a href={settingsApi.exportUrl()} target="_blank" rel="noreferrer">
                <Btn variant="secondary">{t('settings.exportData')}</Btn>
              </a>
              <Btn variant="danger" onClick={wipe}>
                {t('settings.wipeData')}
              </Btn>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}

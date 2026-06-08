import { useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { usersApi } from '@/api/users';
import { carsApi } from '@/api/cars';
import { apiErrorMessage } from '@/api/client';
import { useApi } from '@/hooks/useApi';
import { useUiStore } from '@/stores/uiStore';
import {
  Badge,
  Btn,
  Card,
  Checkbox,
  Column,
  ErrorState,
  FormField,
  Input,
  LoadingState,
  Modal,
  Select,
  Table,
} from '@/components/common';
import { initials } from '@/lib/format';
import type { CreateUserRequest, Locale, User } from '@/types';

export function UsersTab() {
  const { t } = useTranslation();
  const pushToast = useUiStore((s) => s.pushToast);
  const { data, loading, error, reload } = useApi(() => usersApi.list(), []);
  const [modalOpen, setModalOpen] = useState(false);

  async function toggleActive(user: User) {
    try {
      await usersApi.update(user.id, { is_active: !user.is_active });
      pushToast(t('common.saved'), 'success');
      reload();
    } catch (err) {
      pushToast(apiErrorMessage(err), 'error');
    }
  }

  const columns: Column<User>[] = [
    {
      key: 'name',
      header: t('admin.usersName'),
      render: (u) => (
        <span className="flex items-center gap-2">
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-primary text-[11px] font-semibold text-white">
            {initials(u.full_name || u.username)}
          </span>
          <span>
            <span className="block font-medium">{u.full_name}</span>
            <span className="block text-xs text-text-muted">{u.email}</span>
          </span>
        </span>
      ),
    },
    { key: 'username', header: t('admin.usersUsername'), render: (u) => <span className="font-mono text-xs">{u.username}</span> },
    {
      key: 'role',
      header: t('admin.usersRole'),
      render: (u) => (
        <Badge variant={u.is_admin ? 'purple' : 'gray'}>
          {u.is_admin ? t('admin.roleAdmin') : t('admin.roleUser')}
        </Badge>
      ),
    },
    { key: 'cars', header: t('admin.usersCars'), render: (u) => u.cars.map((c) => c.name).join(', ') || '—' },
    {
      key: 'status',
      header: t('admin.usersStatus'),
      render: (u) => (
        <Badge variant={u.is_active ? 'green' : 'gray'}>
          {u.is_active ? t('common.active') : t('common.inactive')}
        </Badge>
      ),
    },
    {
      key: 'actions',
      header: t('common.actions'),
      align: 'right',
      render: (u) => (
        <Btn variant="secondary" size="sm" onClick={() => toggleActive(u)}>
          {u.is_active ? t('admin.usersDeactivate') : t('admin.usersActivate')}
        </Btn>
      ),
    },
  ];

  return (
    <div>
      <div className="mb-3 flex justify-end">
        <Btn onClick={() => setModalOpen(true)}>{t('admin.usersAdd')}</Btn>
      </div>
      {loading && <LoadingState />}
      {error && <ErrorState message={error} onRetry={reload} />}
      {data && (
        <Card padded={false} className="p-2">
          <Table columns={columns} rows={data} rowKey={(u) => u.id} emptyMsg={t('admin.usersEmpty')} />
        </Card>
      )}

      <UserModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onSaved={() => {
          setModalOpen(false);
          reload();
        }}
      />
    </div>
  );
}

function UserModal({ open, onClose, onSaved }: { open: boolean; onClose: () => void; onSaved: () => void }) {
  const { t } = useTranslation();
  const pushToast = useUiStore((s) => s.pushToast);
  const cars = useApi(() => carsApi.list(), open ? [] : ['closed']);

  const [form, setForm] = useState<CreateUserRequest>({
    username: '',
    email: '',
    full_name: '',
    password: '',
    is_admin: false,
    locale: 'sk',
    car_ids: [],
  });
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  function set<K extends keyof CreateUserRequest>(key: K, value: CreateUserRequest[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  function toggleCar(id: number) {
    setForm((f) => ({
      ...f,
      car_ids: f.car_ids.includes(id) ? f.car_ids.filter((c) => c !== id) : [...f.car_ids, id],
    }));
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setErr(null);
    try {
      await usersApi.create(form);
      pushToast(t('common.created'), 'success');
      onSaved();
    } catch (e2) {
      setErr(apiErrorMessage(e2));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={t('admin.userModalTitle')} maxWidth={520}>
      <form onSubmit={submit} className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-3">
          <FormField label={t('admin.usersName')} required>
            <Input value={form.full_name} onChange={(e) => set('full_name', e.target.value)} required />
          </FormField>
          <FormField label={t('admin.usersUsername')} required>
            <Input value={form.username} onChange={(e) => set('username', e.target.value)} required />
          </FormField>
        </div>
        <FormField label={t('admin.usersEmail')} required>
          <Input type="email" value={form.email} onChange={(e) => set('email', e.target.value)} required />
        </FormField>
        <div className="grid grid-cols-2 gap-3">
          <FormField label={t('admin.userPassword')} required>
            <Input type="password" value={form.password} onChange={(e) => set('password', e.target.value)} required />
          </FormField>
          <FormField label={t('admin.userLocale')}>
            <Select value={form.locale} onChange={(e) => set('locale', e.target.value as Locale)}>
              <option value="sk">{t('settings.langSk')}</option>
              <option value="en">{t('settings.langEn')}</option>
            </Select>
          </FormField>
        </div>
        <Checkbox
          id="user-is-admin"
          label={t('admin.userIsAdmin')}
          checked={form.is_admin}
          onChange={(e) => set('is_admin', e.target.checked)}
        />

        <FormField label={t('admin.userAssignCars')}>
          <div className="flex flex-wrap gap-2">
            {(cars.data ?? []).map((c) => (
              <Checkbox
                key={c.id}
                id={`car-${c.id}`}
                label={c.name}
                checked={form.car_ids.includes(c.id)}
                onChange={() => toggleCar(c.id)}
              />
            ))}
            {cars.data && cars.data.length === 0 && (
              <span className="text-xs text-text-faint">{t('cars.empty')}</span>
            )}
          </div>
        </FormField>

        {err && <p className="text-sm text-state-red">{err}</p>}

        <div className="mt-2 flex justify-end gap-2">
          <Btn variant="secondary" type="button" onClick={onClose}>
            {t('common.cancel')}
          </Btn>
          <Btn type="submit" disabled={submitting}>
            {submitting ? t('common.saving') : t('common.save')}
          </Btn>
        </div>
      </form>
    </Modal>
  );
}

export default UsersTab;

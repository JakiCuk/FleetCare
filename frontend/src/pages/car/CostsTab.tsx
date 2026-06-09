import { useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { expensesApi } from '@/api/expenses';
import { apiErrorMessage } from '@/api/client';
import { useApi } from '@/hooks/useApi';
import { useUiStore } from '@/stores/uiStore';
import {
  Badge,
  Btn,
  Card,
  Column,
  ErrorState,
  FormField,
  Input,
  LoadingState,
  Modal,
  PeriodSelector,
  Select,
  Table,
  defaultPeriod,
} from '@/components/common';
import type { PeriodValue } from '@/components/common';
import { CostPieChart } from '@/components/charts';
import { expenseCategoryHex } from '@/lib/colors';
import { formatDate, formatMoney, todayIso } from '@/lib/format';
import type { ChipVariant, Expense, ExpenseCategory } from '@/types';

const categoryVariant: Record<ExpenseCategory, ChipVariant> = {
  fuel: 'blue',
  service: 'yellow',
  documents: 'purple',
  tires: 'green',
  other: 'gray',
};

export function CostsTab({ carId }: { carId: number }) {
  const { t } = useTranslation();
  const pushToast = useUiStore((s) => s.pushToast);
  const [period, setPeriod] = useState<PeriodValue>(() => defaultPeriod());
  const range = { from_date: period.from_date, to_date: period.to_date };
  const list = useApi(() => expensesApi.list(carId, range), [carId, period.from_date, period.to_date]);
  const breakdown = useApi(
    () => expensesApi.breakdown(carId, range),
    [carId, period.from_date, period.to_date],
  );
  const [modalOpen, setModalOpen] = useState(false);

  function categoryLabel(c: ExpenseCategory): string {
    return t(`costs.cat${c.charAt(0).toUpperCase()}${c.slice(1)}`);
  }

  async function remove(exp: Expense) {
    if (!window.confirm(t('common.confirmDelete'))) return;
    try {
      await expensesApi.remove(exp.id);
      pushToast(t('common.deleted'), 'success');
      list.reload();
      breakdown.reload();
    } catch (err) {
      pushToast(apiErrorMessage(err), 'error');
    }
  }

  const columns: Column<Expense>[] = [
    { key: 'date', header: t('costs.colDate'), render: (e) => formatDate(e.occurred_at) },
    { key: 'desc', header: t('costs.colDescription'), render: (e) => e.description },
    {
      key: 'cat',
      header: t('costs.colCategory'),
      render: (e) => <Badge variant={categoryVariant[e.category]}>{categoryLabel(e.category)}</Badge>,
    },
    { key: 'amount', header: t('costs.colAmount'), align: 'right', render: (e) => formatMoney(e.amount) },
    {
      key: 'actions',
      header: t('common.actions'),
      align: 'right',
      render: (e) => (
        <Btn variant="danger" size="sm" onClick={() => remove(e)}>
          {t('common.delete')}
        </Btn>
      ),
    },
  ];

  return (
    <div>
      <div className="mb-4">
        <PeriodSelector value={period} onChange={setPeriod} />
      </div>
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-[260px_1fr]">
      <Card title={t('costs.title')}>
        {breakdown.loading && <LoadingState />}
        {breakdown.error && <ErrorState message={breakdown.error} onRetry={breakdown.reload} />}
        {breakdown.data && (
          <>
            {breakdown.data.breakdown.some((b) => b.amount > 0) ? (
              <CostPieChart data={breakdown.data.breakdown} />
            ) : (
              <p className="py-6 text-center text-sm text-text-faint">{t('common.noData')}</p>
            )}
            <ul className="mt-3 flex flex-col gap-1.5">
              {breakdown.data.breakdown.map((b) => (
                <li key={b.category} className="flex items-center justify-between text-[13px]">
                  <span className="flex items-center gap-2">
                    <span
                      className="inline-block h-2.5 w-2.5 rounded-sm"
                      style={{ backgroundColor: expenseCategoryHex[b.category] ?? expenseCategoryHex.other }}
                    />
                    {categoryLabel(b.category)}
                  </span>
                  <span className="font-medium">{formatMoney(b.amount)}</span>
                </li>
              ))}
            </ul>
            <div className="mt-3 flex items-center justify-between border-t border-border-soft pt-2 text-sm font-semibold">
              <span>{t('costs.total')}</span>
              <span>{formatMoney(breakdown.data.total)}</span>
            </div>
          </>
        )}
      </Card>

      <div>
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-text">{t('costs.expenses')}</h3>
          <Btn onClick={() => setModalOpen(true)}>{t('costs.addExpense')}</Btn>
        </div>
        {list.loading && <LoadingState />}
        {list.error && <ErrorState message={list.error} onRetry={list.reload} />}
        {list.data && (
          <Card padded={false} className="p-2">
            <Table columns={columns} rows={list.data} rowKey={(e) => e.id} emptyMsg={t('costs.empty')} />
          </Card>
        )}
      </div>

      <ExpenseModal
        open={modalOpen}
        carId={carId}
        onClose={() => setModalOpen(false)}
        onSaved={() => {
          setModalOpen(false);
          list.reload();
          breakdown.reload();
        }}
      />
      </div>
    </div>
  );
}

function ExpenseModal({
  open,
  carId,
  onClose,
  onSaved,
}: {
  open: boolean;
  carId: number;
  onClose: () => void;
  onSaved: () => void;
}) {
  const { t } = useTranslation();
  const pushToast = useUiStore((s) => s.pushToast);
  const [occurredAt, setOccurredAt] = useState(todayIso());
  const [description, setDescription] = useState('');
  const [amount, setAmount] = useState('');
  const [category, setCategory] = useState<ExpenseCategory>('other');
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setErr(null);
    try {
      await expensesApi.create(carId, {
        occurred_at: occurredAt,
        description,
        amount: Number(amount),
        category,
      });
      pushToast(t('common.created'), 'success');
      onSaved();
    } catch (e2) {
      setErr(apiErrorMessage(e2));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={t('costs.modalTitle')} maxWidth={460}>
      <form onSubmit={submit} className="flex flex-col gap-4">
        <FormField label={t('costs.fieldDate')} required>
          <Input type="date" value={occurredAt} onChange={(e) => setOccurredAt(e.target.value)} required />
        </FormField>
        <FormField label={t('costs.fieldDescription')} required>
          <Input value={description} onChange={(e) => setDescription(e.target.value)} required />
        </FormField>
        <div className="grid grid-cols-2 gap-3">
          <FormField label={t('costs.fieldAmount')} required>
            <Input type="number" step="0.01" value={amount} onChange={(e) => setAmount(e.target.value)} required />
          </FormField>
          <FormField label={t('costs.fieldCategory')}>
            <Select value={category} onChange={(e) => setCategory(e.target.value as ExpenseCategory)}>
              <option value="fuel">{t('costs.catFuel')}</option>
              <option value="service">{t('costs.catService')}</option>
              <option value="documents">{t('costs.catDocuments')}</option>
              <option value="tires">{t('costs.catTires')}</option>
              <option value="other">{t('costs.catOther')}</option>
            </Select>
          </FormField>
        </div>

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

export default CostsTab;

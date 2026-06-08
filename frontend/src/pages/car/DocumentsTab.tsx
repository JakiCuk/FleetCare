import { useMemo, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { documentsApi } from '@/api/documents';
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
  Select,
  StatusChip,
  Table,
} from '@/components/common';
import { formatDate, formatMoney, todayIso } from '@/lib/format';
import type { ChipVariant } from '@/types';

type DocKind = 'STK' | 'PZP' | 'KASKO' | 'SK' | 'AT' | 'CZ';

interface DocRow {
  id: number;
  kind: DocKind;
  validUntil: string | null;
  daysLeft: number | null;
  cost: number | null;
  provider: string | null;
}

const kindVariant: Record<DocKind, ChipVariant> = {
  STK: 'blue',
  PZP: 'purple',
  KASKO: 'orange',
  SK: 'green',
  AT: 'green',
  CZ: 'green',
};

export function DocumentsTab({ carId }: { carId: number }) {
  const { t } = useTranslation();
  const pushToast = useUiStore((s) => s.pushToast);
  const { data, loading, error, reload } = useApi(() => documentsApi.bundle(carId), [carId]);
  const [modalOpen, setModalOpen] = useState(false);

  const rows = useMemo<DocRow[]>(() => {
    if (!data) return [];
    const out: DocRow[] = [];
    for (const s of data.stk) {
      out.push({ id: s.id, kind: 'STK', validUntil: s.valid_until, daysLeft: s.days_left, cost: s.cost, provider: s.provider });
    }
    for (const i of data.insurance) {
      out.push({ id: i.id, kind: i.type, validUntil: i.valid_until, daysLeft: i.days_left, cost: i.cost, provider: i.provider });
    }
    for (const v of data.vignettes) {
      out.push({ id: v.id, kind: v.country as DocKind, validUntil: v.valid_until, daysLeft: v.days_left, cost: v.cost, provider: v.provider });
    }
    return out;
  }, [data]);

  async function remove(row: DocRow) {
    if (!window.confirm(t('common.confirmDelete'))) return;
    try {
      if (row.kind === 'STK') await documentsApi.removeStk(row.id);
      else if (row.kind === 'PZP' || row.kind === 'KASKO') await documentsApi.removeInsurance(row.id);
      else await documentsApi.removeVignette(row.id);
      pushToast(t('common.deleted'), 'success');
      reload();
    } catch (err) {
      pushToast(apiErrorMessage(err), 'error');
    }
  }

  const columns: Column<DocRow>[] = [
    { key: 'type', header: t('documents.colType'), render: (r) => <Badge variant={kindVariant[r.kind] ?? 'gray'}>{r.kind}</Badge> },
    { key: 'validUntil', header: t('documents.colValidUntil'), render: (r) => formatDate(r.validUntil) },
    {
      key: 'remaining',
      header: t('documents.colRemaining'),
      render: (r) => <StatusChip label="" days={r.daysLeft} urgentThreshold={r.kind === 'STK' || r.kind === 'PZP' || r.kind === 'KASKO' ? 14 : 7} />,
    },
    { key: 'cost', header: t('documents.colCost'), align: 'right', render: (r) => formatMoney(r.cost) },
    { key: 'provider', header: t('documents.colProvider'), render: (r) => r.provider ?? '—' },
    {
      key: 'actions',
      header: t('common.actions'),
      align: 'right',
      render: (r) => (
        <Btn variant="danger" size="sm" onClick={() => remove(r)}>
          {t('common.delete')}
        </Btn>
      ),
    },
  ];

  return (
    <div>
      <div className="mb-4 flex justify-end">
        <Btn onClick={() => setModalOpen(true)}>{t('documents.add')}</Btn>
      </div>

      {loading && <LoadingState />}
      {error && <ErrorState message={error} onRetry={reload} />}
      {data && (
        <Card padded={false} className="p-2">
          <Table columns={columns} rows={rows} rowKey={(r) => `${r.kind}-${r.id}`} emptyMsg={t('documents.empty')} />
        </Card>
      )}

      <DocumentModal
        carId={carId}
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onSaved={() => {
          reload();
          setModalOpen(false);
        }}
      />
    </div>
  );
}

function DocumentModal({
  carId,
  open,
  onClose,
  onSaved,
}: {
  carId: number;
  open: boolean;
  onClose: () => void;
  onSaved: () => void;
}) {
  const { t } = useTranslation();
  const pushToast = useUiStore((s) => s.pushToast);
  const [docType, setDocType] = useState<DocKind>('STK');
  const [validFrom, setValidFrom] = useState(todayIso());
  const [validUntil, setValidUntil] = useState(todayIso());
  const [cost, setCost] = useState('');
  const [provider, setProvider] = useState('');
  const [policyNumber, setPolicyNumber] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setErr(null);
    const costNum = cost ? Number(cost) : null;
    try {
      if (docType === 'STK') {
        await documentsApi.createStk(carId, {
          inspected_at: validFrom,
          valid_until: validUntil,
          cost: costNum,
          provider: provider || null,
        });
      } else if (docType === 'PZP' || docType === 'KASKO') {
        await documentsApi.createInsurance(carId, {
          type: docType,
          provider: provider || null,
          policy_number: policyNumber || null,
          valid_from: validFrom,
          valid_until: validUntil,
          cost: costNum,
        });
      } else {
        await documentsApi.createVignette(carId, {
          country: docType,
          valid_from: validFrom,
          valid_until: validUntil,
          cost: costNum,
          provider: provider || null,
        });
      }
      pushToast(t('common.created'), 'success');
      onSaved();
    } catch (e2) {
      setErr(apiErrorMessage(e2));
    } finally {
      setSubmitting(false);
    }
  }

  const isInsurance = docType === 'PZP' || docType === 'KASKO';

  return (
    <Modal open={open} onClose={onClose} title={t('documents.modalTitle')} maxWidth={480}>
      <form onSubmit={submit} className="flex flex-col gap-4">
        <FormField label={t('documents.docType')}>
          <Select value={docType} onChange={(e) => setDocType(e.target.value as DocKind)}>
            <option value="STK">{t('documents.typeStk')}</option>
            <option value="PZP">{t('documents.typePzp')}</option>
            <option value="KASKO">{t('documents.typeKasko')}</option>
            <option value="SK">{t('documents.typeVignetteSk')}</option>
            <option value="AT">{t('documents.typeVignetteAt')}</option>
            <option value="CZ">{t('documents.typeVignetteCz')}</option>
          </Select>
        </FormField>
        <div className="grid grid-cols-2 gap-3">
          <FormField label={docType === 'STK' ? t('documents.inspectedAt') : t('documents.validFrom')}>
            <Input type="date" value={validFrom} onChange={(e) => setValidFrom(e.target.value)} />
          </FormField>
          <FormField label={t('documents.validUntil')} required>
            <Input type="date" value={validUntil} onChange={(e) => setValidUntil(e.target.value)} required />
          </FormField>
        </div>
        {isInsurance && (
          <FormField label={t('documents.policyNumber')}>
            <Input value={policyNumber} onChange={(e) => setPolicyNumber(e.target.value)} />
          </FormField>
        )}
        <div className="grid grid-cols-2 gap-3">
          <FormField label={t('documents.colCost')}>
            <Input type="number" value={cost} onChange={(e) => setCost(e.target.value)} />
          </FormField>
          <FormField label={t('documents.colProvider')}>
            <Input value={provider} onChange={(e) => setProvider(e.target.value)} />
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

export default DocumentsTab;

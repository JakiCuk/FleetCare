import { useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { notificationsApi } from '@/api/notifications';
import { apiErrorMessage } from '@/api/client';
import { useUiStore } from '@/stores/uiStore';
import { Btn, Checkbox, FormField, Input, Modal, Select } from '@/components/common';
import type { CreateNotificationRuleRequest, NotificationRule } from '@/types';

export interface RuleCarOption {
  id: number;
  name: string;
}

const ITEM_TYPES = ['stk', 'pzp', 'kasko', 'vignette', 'tires', 'service'] as const;

interface RuleModalProps {
  open: boolean;
  /** Cars the rule can target (the user's cars, or all for admin). */
  cars: RuleCarOption[];
  /** Existing rule for edit mode; null for create. */
  rule: NotificationRule | null;
  onClose: () => void;
  onSaved: () => void;
}

function num(v: string): number | null {
  return v === '' ? null : Number(v);
}

export function RuleModal({ open, cars, rule, onClose, onSaved }: RuleModalProps) {
  const { t } = useTranslation();
  const pushToast = useUiStore((s) => s.pushToast);

  const [carId, setCarId] = useState('');
  const [itemType, setItemType] = useState<string>('stk');
  const [lead1, setLead1] = useState('');
  const [lead2, setLead2] = useState('');
  const [lead3, setLead3] = useState('');
  const [channelEmail, setChannelEmail] = useState(true);
  const [channelMatrix, setChannelMatrix] = useState(false);
  const [isSmart, setIsSmart] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  // Sync form whenever the modal opens (create defaults vs. edit prefill).
  useEffect(() => {
    if (!open) return;
    if (rule) {
      setCarId(String(rule.car_id));
      setItemType(rule.item_type);
      setLead1(rule.lead_days_1 != null ? String(rule.lead_days_1) : '');
      setLead2(rule.lead_days_2 != null ? String(rule.lead_days_2) : '');
      setLead3(rule.lead_days_3 != null ? String(rule.lead_days_3) : '');
      setChannelEmail(rule.channel_email);
      setChannelMatrix(rule.channel_matrix);
      setIsSmart(rule.is_smart);
    } else {
      setCarId(cars[0] ? String(cars[0].id) : '');
      setItemType('stk');
      setLead1('30');
      setLead2('7');
      setLead3('');
      setChannelEmail(true);
      setChannelMatrix(false);
      setIsSmart(false);
    }
    setErr(null);
  }, [open, rule, cars]);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setErr(null);
    const body: CreateNotificationRuleRequest = {
      car_id: Number(carId),
      item_type: itemType,
      lead_days_1: num(lead1),
      lead_days_2: num(lead2),
      lead_days_3: num(lead3),
      channel_email: channelEmail,
      channel_matrix: channelMatrix,
      is_smart: isSmart,
    };
    try {
      if (rule) {
        await notificationsApi.updateRule(rule.id, body);
        pushToast(t('common.saved'), 'success');
      } else {
        await notificationsApi.createRule(body);
        pushToast(t('common.created'), 'success');
      }
      onSaved();
    } catch (e2) {
      setErr(apiErrorMessage(e2));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={t('admin.ruleModalTitle')} maxWidth={460}>
      <form onSubmit={submit} className="flex flex-col gap-4">
        <FormField label={t('admin.rulesCar')} required>
          <Select value={carId} onChange={(e) => setCarId(e.target.value)} required disabled={!!rule}>
            {cars.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </Select>
        </FormField>
        <FormField label={t('admin.rulesItemType')} required>
          <Select value={itemType} onChange={(e) => setItemType(e.target.value)} required disabled={!!rule}>
            {ITEM_TYPES.map((it) => (
              <option key={it} value={it}>
                {t(`admin.ruleItem${it.charAt(0).toUpperCase()}${it.slice(1)}`)}
              </option>
            ))}
          </Select>
        </FormField>
        <div className="grid grid-cols-3 gap-3">
          <FormField label={t('admin.rulesLead1')}>
            <Input type="number" value={lead1} onChange={(e) => setLead1(e.target.value)} />
          </FormField>
          <FormField label={t('admin.rulesLead2')}>
            <Input type="number" value={lead2} onChange={(e) => setLead2(e.target.value)} />
          </FormField>
          <FormField label={t('admin.rulesLead3')}>
            <Input type="number" value={lead3} onChange={(e) => setLead3(e.target.value)} />
          </FormField>
        </div>
        <div className="flex flex-col gap-2">
          <Checkbox
            id="rule-email"
            label={t('notifications.channelEmail')}
            checked={channelEmail}
            onChange={(e) => setChannelEmail(e.target.checked)}
          />
          <Checkbox
            id="rule-matrix"
            label={t('notifications.channelMatrix')}
            checked={channelMatrix}
            onChange={(e) => setChannelMatrix(e.target.checked)}
          />
          <Checkbox
            id="rule-smart"
            label={t('admin.rulesSmart')}
            checked={isSmart}
            onChange={(e) => setIsSmart(e.target.checked)}
          />
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

export default RuleModal;

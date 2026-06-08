import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Btn, PageHeader, Tabs } from '@/components/common';
import type { TabItem } from '@/components/common';
import { RulesTab } from './admin/RulesTab';
import { LogTab } from './admin/LogTab';
import { SmtpTab } from './admin/SmtpTab';
import { MatrixTab } from './admin/MatrixTab';
import { UsersTab } from './admin/UsersTab';
import { TestSendModal } from './admin/TestSendModal';

type AdminTab = 'rules' | 'log' | 'smtp' | 'matrix' | 'users';

export default function AdminPage() {
  const { t } = useTranslation();
  const [tab, setTab] = useState<AdminTab>('rules');
  const [testOpen, setTestOpen] = useState(false);

  const tabs: TabItem[] = [
    { key: 'rules', label: t('admin.tabRules') },
    { key: 'log', label: t('admin.tabLog') },
    { key: 'smtp', label: t('admin.tabSmtp') },
    { key: 'matrix', label: t('admin.tabMatrix') },
    { key: 'users', label: t('admin.tabUsers') },
  ];

  return (
    <div>
      <PageHeader
        title={t('admin.title')}
        actions={
          <Btn variant="secondary" onClick={() => setTestOpen(true)}>
            {t('admin.testSend')}
          </Btn>
        }
      />

      <Tabs items={tabs} active={tab} onChange={(k) => setTab(k as AdminTab)} className="mb-5" />

      {tab === 'rules' && <RulesTab />}
      {tab === 'log' && <LogTab />}
      {tab === 'smtp' && <SmtpTab />}
      {tab === 'matrix' && <MatrixTab />}
      {tab === 'users' && <UsersTab />}

      <TestSendModal open={testOpen} onClose={() => setTestOpen(false)} />
    </div>
  );
}

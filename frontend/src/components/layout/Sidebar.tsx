import { NavLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuthStore } from '@/stores/authStore';
import { initials } from '@/lib/format';
import { cn } from '@/lib/cn';
import { navItems } from './navItems';

/** Fixed dark sidebar, 168px wide (DESIGN_SYSTEM §3). Hidden below md. */
export function Sidebar() {
  const { t } = useTranslation();
  const user = useAuthStore((s) => s.user);

  return (
    <aside className="fixed inset-y-0 left-0 z-40 hidden w-sidebar flex-col bg-sidebar text-white md:flex">
      <div className="flex items-center gap-2 px-4 py-5 text-base font-bold">
        <span>🚗</span>
        <span>FleetCare</span>
      </div>

      <nav className="flex-1 px-2">
        {navItems
          .filter((item) => !item.adminOnly || user?.is_admin)
          .map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                cn(
                  'mb-0.5 flex items-center gap-2.5 rounded-md px-3 py-2 text-[13px] font-medium transition',
                  isActive
                    ? 'bg-primary text-white'
                    : 'text-white/70 hover:bg-white/10 hover:text-white',
                )
              }
            >
              <span className="w-4 text-center">{item.icon}</span>
              <span>{t(item.labelKey)}</span>
            </NavLink>
          ))}
      </nav>

      {user && (
        <div className="border-t border-white/10 px-3 py-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-semibold">
              {initials(user.full_name || user.username)}
            </div>
            <div className="min-w-0">
              <div className="truncate text-xs font-semibold">{user.full_name}</div>
              <div className="truncate text-[11px] text-white/60">
                {user.is_admin ? t('admin.roleAdmin') : t('admin.roleUser')}
              </div>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
}

export default Sidebar;

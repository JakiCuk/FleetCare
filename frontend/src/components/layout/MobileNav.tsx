import { NavLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuthStore } from '@/stores/authStore';
import { cn } from '@/lib/cn';
import { navItems } from './navItems';

/** Bottom tab bar for screens < md (DESIGN_SYSTEM §3 mobile). */
export function MobileNav() {
  const { t } = useTranslation();
  const user = useAuthStore((s) => s.user);

  const items = navItems.filter((item) => !item.adminOnly || user?.is_admin);

  return (
    <nav className="fixed inset-x-0 bottom-0 z-40 flex border-t border-border bg-sidebar text-white md:hidden">
      {items.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.to === '/'}
          className={({ isActive }) =>
            cn(
              'flex flex-1 flex-col items-center gap-0.5 py-2 text-[10px] font-medium transition',
              isActive ? 'text-primary' : 'text-white/70',
            )
          }
        >
          <span className="text-base leading-none">{item.icon}</span>
          <span className="truncate">{t(item.labelKey)}</span>
        </NavLink>
      ))}
    </nav>
  );
}

export default MobileNav;

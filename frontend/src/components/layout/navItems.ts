export interface NavItem {
  to: string;
  /** i18n key under nav.* */
  labelKey: string;
  icon: string;
  /** Restrict to admins. */
  adminOnly?: boolean;
}

export const navItems: NavItem[] = [
  { to: '/', labelKey: 'nav.dashboard', icon: '⊞' },
  { to: '/cars', labelKey: 'nav.cars', icon: '🚗' },
  { to: '/notifications', labelKey: 'nav.notifications', icon: '🔔' },
  { to: '/admin', labelKey: 'nav.admin', icon: '⚙', adminOnly: true },
  { to: '/settings', labelKey: 'nav.settings', icon: '◎', adminOnly: true },
];

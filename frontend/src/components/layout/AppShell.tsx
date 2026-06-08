import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { MobileNav } from './MobileNav';
import { Toaster } from '@/components/common';

/** App chrome: fixed sidebar (desktop) + content area + mobile bottom nav. */
export function AppShell() {
  return (
    <div className="min-h-full bg-bg">
      <Sidebar />
      <main className="md:ml-sidebar">
        <div className="mx-auto max-w-content px-4 py-6 pb-24 md:px-8 md:py-7 md:pb-7">
          <Outlet />
        </div>
      </main>
      <MobileNav />
      <Toaster />
    </div>
  );
}

export default AppShell;

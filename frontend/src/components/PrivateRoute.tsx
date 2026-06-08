import type { ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import { LoadingState } from '@/components/common';

/** Guards routes: redirects to /login when there's no authenticated user. */
export function PrivateRoute({ children }: { children: ReactNode }) {
  const user = useAuthStore((s) => s.user);
  const initializing = useAuthStore((s) => s.initializing);

  if (initializing) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingState />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

/** Admin-only guard for /admin. */
export function AdminRoute({ children }: { children: ReactNode }) {
  const user = useAuthStore((s) => s.user);
  if (user && !user.is_admin) {
    return <Navigate to="/" replace />;
  }
  return <>{children}</>;
}

export default PrivateRoute;

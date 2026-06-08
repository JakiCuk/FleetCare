import { useEffect } from 'react';
import { RouterProvider } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { router } from './router';
import { useAuthStore } from '@/stores/authStore';
import { useUiStore } from '@/stores/uiStore';

export default function App() {
  const bootstrap = useAuthStore((s) => s.bootstrap);
  const user = useAuthStore((s) => s.user);
  const locale = useUiStore((s) => s.locale);
  const setLocale = useUiStore((s) => s.setLocale);
  const { i18n } = useTranslation();

  // Recover session from the refresh cookie on first load.
  useEffect(() => {
    void bootstrap();
  }, [bootstrap]);

  // Keep i18n language in sync with the chosen locale.
  useEffect(() => {
    if (i18n.language !== locale) void i18n.changeLanguage(locale);
  }, [locale, i18n]);

  // Adopt the user's saved locale once they log in.
  useEffect(() => {
    if (user?.locale && user.locale !== locale) {
      setLocale(user.locale);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.locale]);

  return <RouterProvider router={router} />;
}

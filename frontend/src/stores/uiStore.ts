import { create } from 'zustand';
import type { Locale } from '@/types';
import i18n from '@/i18n';

const LOCALE_KEY = 'fleetcare.locale';

export type ToastVariant = 'success' | 'error' | 'info';

export interface Toast {
  id: number;
  message: string;
  variant: ToastVariant;
}

interface UiState {
  locale: Locale;
  mobileMenuOpen: boolean;
  toasts: Toast[];
  setLocale: (locale: Locale) => void;
  toggleMobileMenu: (open?: boolean) => void;
  pushToast: (message: string, variant?: ToastVariant) => void;
  dismissToast: (id: number) => void;
}

function readStoredLocale(): Locale {
  if (typeof localStorage !== 'undefined') {
    const stored = localStorage.getItem(LOCALE_KEY);
    if (stored === 'sk' || stored === 'en') return stored;
  }
  return 'sk';
}

let toastSeq = 0;

export const useUiStore = create<UiState>((set, get) => ({
  locale: readStoredLocale(),
  mobileMenuOpen: false,
  toasts: [],

  setLocale: (locale) => {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(LOCALE_KEY, locale);
    }
    void i18n.changeLanguage(locale);
    set({ locale });
  },

  toggleMobileMenu: (open) =>
    set((s) => ({ mobileMenuOpen: open ?? !s.mobileMenuOpen })),

  pushToast: (message, variant = 'info') => {
    const id = ++toastSeq;
    set((s) => ({ toasts: [...s.toasts, { id, message, variant }] }));
    setTimeout(() => get().dismissToast(id), 4000);
  },

  dismissToast: (id) =>
    set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}));

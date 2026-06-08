import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import sk from './sk.json';
import en from './en.json';

const LOCALE_KEY = 'fleetcare.locale';

function initialLocale(): 'sk' | 'en' {
  if (typeof localStorage !== 'undefined') {
    const stored = localStorage.getItem(LOCALE_KEY);
    if (stored === 'sk' || stored === 'en') return stored;
  }
  return 'sk';
}

void i18n.use(initReactI18next).init({
  resources: {
    sk: { translation: sk },
    en: { translation: en },
  },
  lng: initialLocale(),
  fallbackLng: 'sk',
  interpolation: { escapeValue: false },
  returnNull: false,
});

export default i18n;

import { ref, computed } from 'vue';
import enUS from './locales/en-US.js'; // Changed from .locales to ./locales
import frFR from './locales/fr-FR.js';

// Available locales
const locales = {
  'en-US': enUS,
  'fr-FR': frFR,
};

// Current locale (default to browser language or fallback to English)
const currentLocale = ref(
  navigator.language in locales ? navigator.language : 'en-US'
);

/**
 * Changes the current application locale
 * @param {string} locale - The locale code to change to
 */
export function setLocale(locale: string): void {
  if (locales[locale]) {
    currentLocale.value = locale;
    document.documentElement.setAttribute('lang', locale);
  } else {
    console.warn(`Locale ${locale} is not supported`);
  }
}

/**
 * Gets the translation for a given key
 * @param {string} key - The translation key to lookup
 * @param {Record<string, any>} params - Optional parameters for dynamic translation
 * @returns {string} Translated text
 */
export function t(key: string, params: Record<string, any> = {}): string {
  const locale = locales[currentLocale.value];

  if (!locale) {
    console.warn(`Locale ${currentLocale.value} is not loaded`);
    return key;
  }

  const keys = key.split('.');
  let value = locale;

  for (const k of keys) {
    if (value[k] === undefined) {
      console.warn(`Translation key not found: ${key}`);
      return key;
    }
    value = value[k];
  }

  if (typeof value === 'string') {
    // Replace parameters in the translation string
    return Object.entries(params).reduce(
      (str, [key, val]) => str.replace(new RegExp(`{${key}}`, 'g'), val),
      value
    );
  }

  return key;
}

export const i18n = {
  t,
  setLocale,
  currentLocale: computed(() => currentLocale.value),
  availableLocales: Object.keys(locales),
};

export default i18n;

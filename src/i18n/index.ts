import { createI18n } from 'vue-i18n'
import enUS from './locales/en-US'
import frFR from './locales/fr-FR'

const messages: Record<string, any> = {
  'en-US': enUS,
  'fr-FR': frFR,
}

const locale = localStorage.getItem('userLocale') || navigator.language || 'en-US'

export const i18n = createI18n({
  legacy: false,
  locale: messages[locale] ? locale : 'en-US',
  fallbackLocale: 'en-US',
  messages,
})




// Default to browser language or fall back to English
const getBrowserLocale = (): string => {
  const navigatorLocale = navigator.languages !== undefined
    ? navigator.languages[0]
    : navigator.language

  if (!navigatorLocale) {
    return 'en-US'
  }

  // Check if we have an exact match
  if (messages[navigatorLocale]) {
    return navigatorLocale
  }

  // Try to match just the language part (e.g. 'en' from 'en-GB')
  const languageCode = navigatorLocale.split('-')[0]
  for (const locale in messages) {
    if (locale.startsWith(languageCode)) {
      return locale
    }
  }

  return 'en-US'
}
// Initialize from localStorage if available



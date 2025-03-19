import { ref, computed } from 'vue'
import enUS from './locales/en-US'
import frFR from './locales/fr-FR'

// Type definitions for translation handling
type LocaleMessages = {
  [key: string]: any
}

// Available locales with their data
const messages: Record<string, LocaleMessages> = {
  'en-US': enUS,
  'fr-FR': frFR
}

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

// Current locale state
const currentLocale = ref(getBrowserLocale())

/**
 * Get a nested property from an object using a dot-notation path
 * @param obj The object to get the value from
 * @param path The path in dot notation format (e.g. "common.button.submit")
 * @returns The value at the path or undefined if not found
 */
const getNestedValue = (obj: any, path: string): any => {
  return path.split('.').reduce((prev, curr) => {
    return prev && prev[curr] !== undefined ? prev[curr] : undefined
  }, obj)
}

/**
 * Translate a key with optional parameter replacement
 * @param key Translation key in dot notation
 * @param params Optional parameters to replace in the translation
 * @returns Translated string or the key if translation not found
 */
const t = (key: string, params?: Record<string, any>): string => {
  const locale = currentLocale.value
  const message = getNestedValue(messages[locale], key)

  if (!message) {
    console.warn(`Translation key not found: ${key} in locale: ${locale}`)
    return key
  }

  if (typeof message !== 'string') {
    console.warn(`Translation key ${key} is not a string in locale: ${locale}`)
    return key
  }

  // Replace params in the message if provided
  if (params) {
    return Object.entries(params).reduce((acc, [key, value]) => {
      return acc.replace(new RegExp(`{${key}}`, 'g'), String(value))
    }, message)
  }

  return message
}

/**
 * Set the current locale
 * @param locale The locale code to set as current
 */
const setLocale = (locale: string): void => {
  if (messages[locale]) {
    currentLocale.value = locale
    // Store the locale preference
    localStorage.setItem('userLocale', locale)
    // Optional: update document language for accessibility
    document.documentElement.lang = locale
  } else {
    console.warn(`Locale not supported: ${locale}`)
  }
}

// Initialize from localStorage if available
const initLocale = (): void => {
  const savedLocale = localStorage.getItem('userLocale')
  if (savedLocale && messages[savedLocale]) {
    currentLocale.value = savedLocale
    document.documentElement.lang = savedLocale
  }
}

// Run initialization
initLocale()

// Export the i18n composable
export const i18n = {
  t,
  setLocale,
  currentLocale: computed(() => currentLocale.value),
  availableLocales: Object.keys(messages)
}

// Export individual functions for more flexibility
export { t, setLocale }

export default i18n

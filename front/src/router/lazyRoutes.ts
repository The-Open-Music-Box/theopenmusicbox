/**
 * Lazy-loaded route components for better code splitting
 * This reduces the initial bundle size by loading routes on demand
 */

import { defineAsyncComponent, type Component } from 'vue'
import { logger } from '@/utils/logger'

/**
 * Create a lazy-loaded component with error handling and loading states
 */
function createLazyComponent(importFn: () => Promise<{ default: Component }>, componentName: string) {
  return defineAsyncComponent({
    loader: importFn,
    loadingComponent: {
      template: '<div class="flex justify-center items-center p-8"><div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div></div>'
    },
    errorComponent: {
      template: '<div class="text-red-500 p-4">Failed to load component. Please refresh the page.</div>'
    },
    delay: 200,
    timeout: 10000,
    onError: (error) => {
      logger.error(`Failed to load component: ${componentName}`, { error }, 'LazyRoutes')
    }
  })
}

// Lazy-loaded route components
export const HomePage = createLazyComponent(
  () => import('../views/HomePage.vue'),
  'HomePage'
)

export const AboutPage = createLazyComponent(
  () => import('../views/AboutPage.vue'),
  'AboutPage'
)

export const SettingsPage = createLazyComponent(
  () => import('../views/SettingsPage.vue'),
  'SettingsPage'
)

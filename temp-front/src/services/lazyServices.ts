/**
 * Lazy-loaded services to reduce initial bundle size
 * Services are loaded only when needed
 */

import { logger } from '@/utils/logger'

/**
 * Lazy load Socket.IO client only when needed
 */
export async function loadSocketService() {
  try {
    const { default: socketService } = await import('./socketService')
    return socketService
  } catch (error) {
    logger.error('Failed to load socket service', { error }, 'LazyServices')
    throw error
  }
}

/**
 * Lazy load data service only when needed
 */
export async function loadDataService() {
  try {
    const { default: dataService } = await import('./dataService')
    return dataService
  } catch (error) {
    logger.error('Failed to load data service', { error }, 'LazyServices')
    throw error
  }
}

/**
 * Lazy load upload store only when upload functionality is needed
 */
export async function loadUploadStore() {
  try {
    const { useUploadStore } = await import('../stores/uploadStore')
    return useUploadStore
  } catch (error) {
    logger.error('Failed to load upload store', { error }, 'LazyServices')
    throw error
  }
}

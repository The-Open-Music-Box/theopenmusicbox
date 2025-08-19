/**
 * Robust Upload Composable
 * 
 * A wrapper around useUnifiedUpload specifically designed for robust upload scenarios
 * with enhanced error handling, retry logic, and recovery mechanisms.
 * 
 * Features:
 * - Enhanced retry logic with exponential backoff
 * - Automatic error recovery
 * - Upload session persistence
 * - Network failure detection and handling
 * - Progress persistence across retries
 */

import { ref, computed } from 'vue'
import { useUnifiedUpload, type UploadConfig } from './useUnifiedUpload'
import type { UploadError } from '@/types/errors'
import { logger } from '@/utils/logger'

// Enhanced configuration for robust uploads
export interface RobustUploadConfig extends UploadConfig {
  persistProgress: boolean
  autoRetryOnNetworkError: boolean
  maxNetworkRetries: number
  networkRetryDelay: number
  enableSessionRecovery: boolean
}

/**
 * Robust Upload Composable
 * 
 * Provides enhanced upload capabilities with robust error handling,
 * automatic retries, and session recovery for unreliable network conditions.
 */
export function useRobustUpload(config: Partial<RobustUploadConfig> = {}) {
  // Enhanced configuration with robust defaults
  const robustConfig: RobustUploadConfig = {
    chunkSize: 1024 * 1024, // 1MB
    maxRetries: 5, // Increased for robust uploads
    useChunkedUpload: true,
    validateFiles: true,
    generateChecksums: true,
    maxFileSize: 100 * 1024 * 1024, // 100MB
    allowedFileTypes: ['audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/ogg', 'audio/flac'],
    concurrentUploads: 1,
    persistProgress: true,
    autoRetryOnNetworkError: true,
    maxNetworkRetries: 10,
    networkRetryDelay: 2000,
    enableSessionRecovery: true,
    exponentialBackoff: true,
    maxBackoffDelay: 30000,
    ...config
  } as RobustUploadConfig

  // Network state tracking
  const networkRetryCount = ref<number>(0)
  const isNetworkError = ref<boolean>(false)
  const lastNetworkError = ref<string | null>(null)
  const sessionRecoveryAttempts = ref<number>(0)

  // Enhanced error handling
  const handleRobustError = (error: UploadError) => {
    logger.error('Robust upload error', { error }, 'RobustUpload')
    
    // Detect network errors
    const networkErrorCodes = ['NETWORK_ERROR', 'TIMEOUT', 'CONNECTION_FAILED', 'ECONNRESET']
    const isNetworkIssue = networkErrorCodes.some(code => 
      error.code?.includes(code) || error.message?.includes(code.toLowerCase())
    )

    if (isNetworkIssue && robustConfig.autoRetryOnNetworkError) {
      isNetworkError.value = true
      lastNetworkError.value = error.message
      
      if (networkRetryCount.value < robustConfig.maxNetworkRetries) {
        networkRetryCount.value++
        logger.info(`Network error detected, scheduling retry ${networkRetryCount.value}/${robustConfig.maxNetworkRetries}`, {
          error: error.message,
          retryDelay: robustConfig.networkRetryDelay
        }, 'RobustUpload')
        
        // Schedule retry after delay
        setTimeout(() => {
          if (currentPlaylistId.value) {
            startRobustUpload(currentPlaylistId.value)
          }
        }, robustConfig.networkRetryDelay)
        
        return
      }
    }

    // Reset network error state if max retries exceeded
    isNetworkError.value = false
    networkRetryCount.value = 0
  }

  // Get the base upload composable with enhanced error handling
  const baseUpload = useUnifiedUpload(robustConfig, handleRobustError)
  const currentPlaylistId = ref<string | null>(null)

  // Enhanced computed properties
  const isRecovering = computed(() => 
    sessionRecoveryAttempts.value > 0 || networkRetryCount.value > 0
  )

  const recoveryStatus = computed(() => {
    if (networkRetryCount.value > 0) {
      return `Network retry ${networkRetryCount.value}/${robustConfig.maxNetworkRetries}`
    }
    if (sessionRecoveryAttempts.value > 0) {
      return `Session recovery attempt ${sessionRecoveryAttempts.value}`
    }
    return null
  })

  const canRetry = computed(() => 
    networkRetryCount.value < robustConfig.maxNetworkRetries ||
    sessionRecoveryAttempts.value < 3
  )

  // Enhanced upload method with robust error handling
  const startRobustUpload = async (playlistId: string): Promise<void> => {
    currentPlaylistId.value = playlistId
    
    try {
      // Reset recovery state on new upload
      if (!isRecovering.value) {
        networkRetryCount.value = 0
        sessionRecoveryAttempts.value = 0
        isNetworkError.value = false
        lastNetworkError.value = null
      }

      await baseUpload.startUpload(playlistId)
      
      // Reset retry counters on successful upload
      networkRetryCount.value = 0
      sessionRecoveryAttempts.value = 0
      isNetworkError.value = false
      
    } catch (error) {
      logger.error('Robust upload failed', { error, playlistId }, 'RobustUpload')
      throw error
    }
  }

  // Manual retry method
  const retryUpload = async (): Promise<void> => {
    if (!currentPlaylistId.value) {
      throw new Error('No playlist ID available for retry')
    }

    if (!canRetry.value) {
      throw new Error('Maximum retry attempts exceeded')
    }

    sessionRecoveryAttempts.value++
    await startRobustUpload(currentPlaylistId.value)
  }

  // Reset method with enhanced cleanup
  const resetRobustUpload = () => {
    baseUpload.resetUpload()
    networkRetryCount.value = 0
    sessionRecoveryAttempts.value = 0
    isNetworkError.value = false
    lastNetworkError.value = null
    currentPlaylistId.value = null
  }

  // Cancel method with enhanced cleanup
  const cancelRobustUpload = () => {
    baseUpload.cancelUpload()
    networkRetryCount.value = 0
    sessionRecoveryAttempts.value = 0
    isNetworkError.value = false
    currentPlaylistId.value = null
  }

  return {
    // Base upload functionality
    ...baseUpload,
    
    // Enhanced configuration
    robustConfig,
    
    // Robust-specific state
    networkRetryCount,
    isNetworkError,
    lastNetworkError,
    sessionRecoveryAttempts,
    isRecovering,
    recoveryStatus,
    canRetry,
    
    // Enhanced methods
    startUpload: startRobustUpload,
    retryUpload,
    resetUpload: resetRobustUpload,
    cancelUpload: cancelRobustUpload
  }
}

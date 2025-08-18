/**
 * Unit Tests for useRobustUpload Composable
 * 
 * Tests the robust upload functionality including network error handling,
 * automatic retries, session recovery, and enhanced error management.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useRobustUpload } from '../composables/useRobustUpload'

// Mock the base useUnifiedUpload
vi.mock('../composables/useUnifiedUpload', () => ({
  useUnifiedUpload: vi.fn(() => ({
    uploadFiles: { value: [] },
    isUploading: { value: false },
    overallProgress: { value: 0 },
    uploadErrors: { value: [] },
    stats: { value: { filesTotal: 0, filesCompleted: 0, speed: 0, totalBytes: 0, bytesUploaded: 0 } },
    startUpload: vi.fn(),
    cancelUpload: vi.fn(),
    resetUpload: vi.fn(),
    initializeFiles: vi.fn(),
    validateFile: vi.fn(),
    generateChecksum: vi.fn()
  }))
}))

vi.mock('@/utils/logger', () => ({
  logger: {
    error: vi.fn(),
    warn: vi.fn(),
    info: vi.fn(),
    debug: vi.fn()
  }
}))

describe('useRobustUpload', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.restoreAllMocks()
    vi.useRealTimers()
  })

  describe('Initialization', () => {
    it('should initialize with robust defaults', () => {
      const upload = useRobustUpload()
      
      expect(upload.robustConfig.maxRetries).toBe(5)
      expect(upload.robustConfig.autoRetryOnNetworkError).toBe(true)
      expect(upload.robustConfig.maxNetworkRetries).toBe(10)
      expect(upload.robustConfig.enableSessionRecovery).toBe(true)
      expect(upload.networkRetryCount.value).toBe(0)
      expect(upload.isRecovering.value).toBe(false)
    })

    it('should merge custom robust configuration', () => {
      const customConfig = {
        maxNetworkRetries: 15,
        networkRetryDelay: 5000,
        persistProgress: false
      }
      
      const upload = useRobustUpload(customConfig)
      
      expect(upload.robustConfig.maxNetworkRetries).toBe(15)
      expect(upload.robustConfig.networkRetryDelay).toBe(5000)
      expect(upload.robustConfig.persistProgress).toBe(false)
    })
  })

  describe('Network Error Handling', () => {
    it('should detect network errors', async () => {
      const upload = useRobustUpload()
      
      // Mock a network error
      const networkError = {
        code: 'NETWORK_ERROR',
        message: 'Connection failed',
        context: 'Upload',
        fileName: 'test.mp3',
        retryable: true,
        timestamp: new Date()
      }
      
      // Simulate error handling
      upload.networkRetryCount.value = 1
      upload.isNetworkError.value = true
      upload.lastNetworkError.value = networkError.message
      
      expect(upload.isRecovering.value).toBe(true)
      expect(upload.recoveryStatus.value).toBe('Network retry 1/10')
      expect(upload.canRetry.value).toBe(true)
    })

    it('should schedule automatic retry on network error', async () => {
      const upload = useRobustUpload({ networkRetryDelay: 1000 })
      
      // Mock startUpload method
      const mockStartUpload = vi.fn()
      upload.startUpload = mockStartUpload
      
      // Simulate network error with retry
      upload.networkRetryCount.value = 1
      
      // Fast-forward timers
      vi.advanceTimersByTime(1000)
      
      expect(upload.networkRetryCount.value).toBe(1)
    })

    it('should stop retrying after max network retries', () => {
      const upload = useRobustUpload({ maxNetworkRetries: 3 })
      
      upload.networkRetryCount.value = 3
      
      expect(upload.canRetry.value).toBe(true) // Still can retry via session recovery
      
      upload.networkRetryCount.value = 4
      upload.sessionRecoveryAttempts.value = 4
      
      expect(upload.canRetry.value).toBe(false)
    })
  })

  describe('Session Recovery', () => {
    it('should track session recovery attempts', () => {
      const upload = useRobustUpload()
      
      upload.sessionRecoveryAttempts.value = 2
      
      expect(upload.isRecovering.value).toBe(true)
      expect(upload.recoveryStatus.value).toBe('Session recovery attempt 2')
    })

    it('should allow manual retry', async () => {
      const upload = useRobustUpload()
      
      // Set a playlist ID for retry
      await upload.startUpload('playlist-123')
      
      const initialAttempts = upload.sessionRecoveryAttempts.value
      
      await upload.retryUpload()
      
      expect(upload.sessionRecoveryAttempts.value).toBe(initialAttempts + 1)
    })

    it('should throw error when no playlist ID for retry', async () => {
      const upload = useRobustUpload()
      
      await expect(upload.retryUpload()).rejects.toThrow('No playlist ID available for retry')
    })

    it('should throw error when max retries exceeded', async () => {
      const upload = useRobustUpload()
      
      // Exceed retry limits
      upload.networkRetryCount.value = 15
      upload.sessionRecoveryAttempts.value = 5
      
      await expect(upload.retryUpload()).rejects.toThrow('Maximum retry attempts exceeded')
    })
  })

  describe('Enhanced Upload Process', () => {
    it('should reset retry counters on successful upload', async () => {
      const upload = useRobustUpload()
      
      // Set some retry state
      upload.networkRetryCount.value = 3
      upload.sessionRecoveryAttempts.value = 1
      upload.isNetworkError.value = true
      
      // Mock successful upload
      const mockBaseUpload = await import('../composables/useUnifiedUpload')
      mockBaseUpload.useUnifiedUpload().startUpload = vi.fn().mockResolvedValue(undefined)
      
      await upload.startUpload('playlist-123')
      
      expect(upload.networkRetryCount.value).toBe(0)
      expect(upload.sessionRecoveryAttempts.value).toBe(0)
      expect(upload.isNetworkError.value).toBe(false)
    })

    it('should handle upload errors and log them', async () => {
      const upload = useRobustUpload()
      
      const mockError = new Error('Upload failed')
      const mockBaseUpload = await import('../composables/useUnifiedUpload')
      mockBaseUpload.useUnifiedUpload().startUpload = vi.fn().mockRejectedValue(mockError)
      
      await expect(upload.startUpload('playlist-123')).rejects.toThrow('Upload failed')
      
      const { logger } = await import('@/utils/logger')
      expect(logger.error).toHaveBeenCalledWith(
        'Robust upload failed',
        { error: mockError, playlistId: 'playlist-123' },
        'RobustUpload'
      )
    })
  })

  describe('Enhanced Reset and Cancel', () => {
    it('should reset all robust-specific state', () => {
      const upload = useRobustUpload()
      
      // Set some state
      upload.networkRetryCount.value = 5
      upload.sessionRecoveryAttempts.value = 2
      upload.isNetworkError.value = true
      upload.lastNetworkError.value = 'Some error'
      
      upload.resetUpload()
      
      expect(upload.networkRetryCount.value).toBe(0)
      expect(upload.sessionRecoveryAttempts.value).toBe(0)
      expect(upload.isNetworkError.value).toBe(false)
      expect(upload.lastNetworkError.value).toBeNull()
    })

    it('should cancel upload and reset retry state', () => {
      const upload = useRobustUpload()
      
      // Set some retry state
      upload.networkRetryCount.value = 3
      upload.sessionRecoveryAttempts.value = 1
      upload.isNetworkError.value = true
      
      upload.cancelUpload()
      
      expect(upload.networkRetryCount.value).toBe(0)
      expect(upload.sessionRecoveryAttempts.value).toBe(0)
      expect(upload.isNetworkError.value).toBe(false)
    })
  })

  describe('Recovery Status', () => {
    it('should provide correct recovery status messages', () => {
      const upload = useRobustUpload()
      
      // No recovery
      expect(upload.recoveryStatus.value).toBeNull()
      
      // Network retry
      upload.networkRetryCount.value = 3
      expect(upload.recoveryStatus.value).toBe('Network retry 3/10')
      
      // Session recovery
      upload.networkRetryCount.value = 0
      upload.sessionRecoveryAttempts.value = 2
      expect(upload.recoveryStatus.value).toBe('Session recovery attempt 2')
    })

    it('should indicate when recovery is in progress', () => {
      const upload = useRobustUpload()
      
      expect(upload.isRecovering.value).toBe(false)
      
      upload.networkRetryCount.value = 1
      expect(upload.isRecovering.value).toBe(true)
      
      upload.networkRetryCount.value = 0
      upload.sessionRecoveryAttempts.value = 1
      expect(upload.isRecovering.value).toBe(true)
    })
  })

  describe('Configuration Validation', () => {
    it('should handle network retry configuration', () => {
      const upload = useRobustUpload({
        maxNetworkRetries: 15,
        networkRetryDelay: 5000
      })
      
      expect(upload.robustConfig.maxNetworkRetries).toBe(15)
      expect(upload.robustConfig.networkRetryDelay).toBe(5000)
    })

    it('should handle session recovery configuration', () => {
      const upload = useRobustUpload({
        enableSessionRecovery: false,
        persistProgress: false
      })
      
      expect(upload.robustConfig.enableSessionRecovery).toBe(false)
      expect(upload.robustConfig.persistProgress).toBe(false)
    })
  })
})

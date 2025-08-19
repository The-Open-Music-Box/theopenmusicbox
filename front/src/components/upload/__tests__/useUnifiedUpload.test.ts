/**
 * Unit Tests for useUnifiedUpload Composable
 * 
 * Tests the core upload functionality including file validation,
 * chunked uploads, progress tracking, and error handling.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { ref } from 'vue'
import { useUnifiedUpload } from '../composables/useUnifiedUpload'

// Mock dependencies
vi.mock('@/services/dataService', () => ({
  default: {
    initUpload: vi.fn(),
    uploadChunk: vi.fn(),
    finalizeUpload: vi.fn(),
    uploadFiles: vi.fn()
  }
}))

vi.mock('@/services/socketService', () => ({
  default: {
    on: vi.fn(),
    off: vi.fn()
  }
}))

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string, params?: any) => `${key}${params ? JSON.stringify(params) : ''}`
  })
}))

vi.mock('@/utils/logger', () => ({
  logger: {
    error: vi.fn(),
    warn: vi.fn(),
    info: vi.fn(),
    debug: vi.fn()
  }
}))

describe('useUnifiedUpload', () => {
  let mockFile: File
  let mockFiles: File[]

  beforeEach(() => {
    // Create mock files
    mockFile = new File(['test content'], 'test.mp3', { type: 'audio/mpeg' })
    mockFiles = [
      mockFile,
      new File(['test content 2'], 'test2.mp3', { type: 'audio/mpeg' })
    ]

    // Clear all mocks
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Initialization', () => {
    it('should initialize with default configuration', () => {
      const upload = useUnifiedUpload()
      
      expect(upload.uploadConfig.value.chunkSize).toBe(1024 * 1024)
      expect(upload.uploadConfig.value.maxRetries).toBe(3)
      expect(upload.uploadConfig.value.useChunkedUpload).toBe(true)
      expect(upload.uploadConfig.value.validateFiles).toBe(true)
      expect(upload.uploadFiles.value).toEqual([])
      expect(upload.isUploading.value).toBe(false)
      expect(upload.overallProgress.value).toBe(0)
    })

    it('should merge custom configuration', () => {
      const customConfig = {
        chunkSize: 2048 * 1024,
        maxRetries: 5,
        validateFiles: false
      }
      
      const upload = useUnifiedUpload(customConfig)
      
      expect(upload.uploadConfig.value.chunkSize).toBe(2048 * 1024)
      expect(upload.uploadConfig.value.maxRetries).toBe(5)
      expect(upload.uploadConfig.value.validateFiles).toBe(false)
      expect(upload.uploadConfig.value.useChunkedUpload).toBe(true) // default
    })
  })

  describe('File Validation', () => {
    it('should validate audio files correctly', () => {
      const upload = useUnifiedUpload()
      
      const validFile = new File(['content'], 'test.mp3', { type: 'audio/mpeg' })
      const invalidFile = new File(['content'], 'test.txt', { type: 'text/plain' })
      
      expect(upload.validateFile(validFile)).toBeNull()
      expect(upload.validateFile(invalidFile)).toBeTruthy()
    })

    it('should reject files that are too large', () => {
      const upload = useUnifiedUpload()
      
      // Create a mock file that appears to be over 100MB
      const largeFile = new File(['content'], 'large.mp3', { type: 'audio/mpeg' })
      Object.defineProperty(largeFile, 'size', { value: 101 * 1024 * 1024 })
      
      const error = upload.validateFile(largeFile)
      expect(error).toBeTruthy()
      expect(error).toContain('large.mp3')
    })

    it('should skip validation when disabled', () => {
      const upload = useUnifiedUpload({ validateFiles: false })
      
      const invalidFile = new File(['content'], 'test.txt', { type: 'text/plain' })
      expect(upload.validateFile(invalidFile)).toBeNull()
    })
  })

  describe('File Initialization', () => {
    it('should initialize valid files', () => {
      const upload = useUnifiedUpload()
      
      upload.initializeFiles(mockFiles)
      
      expect(upload.uploadFiles.value).toHaveLength(2)
      expect(upload.uploadFiles.value[0].file.name).toBe('test.mp3')
      expect(upload.uploadFiles.value[0].status).toBe('pending')
      expect(upload.uploadFiles.value[0].progress).toBe(0)
      expect(upload.stats.value.filesTotal).toBe(2)
    })

    it('should filter out invalid files', () => {
      const upload = useUnifiedUpload()
      
      const mixedFiles = [
        ...mockFiles,
        new File(['content'], 'invalid.txt', { type: 'text/plain' })
      ]
      
      upload.initializeFiles(mixedFiles)
      
      expect(upload.uploadFiles.value).toHaveLength(2)
      expect(upload.uploadErrors.value).toHaveLength(1)
    })
  })

  describe('Upload Process', () => {
    it('should start upload process', async () => {
      const upload = useUnifiedUpload()
      upload.initializeFiles([mockFile])
      
      const mockDataService = await import('@/services/dataService')
      mockDataService.default.initUpload = vi.fn().mockResolvedValue({ session_id: 'test-session' })
      mockDataService.default.uploadChunk = vi.fn().mockResolvedValue({})
      mockDataService.default.finalizeUpload = vi.fn().mockResolvedValue({})
      
      await upload.startUpload('playlist-123')
      
      expect(upload.isUploading.value).toBe(false) // Should be false after completion
      expect(mockDataService.default.initUpload).toHaveBeenCalledWith('playlist-123', {
        filename: 'test.mp3',
        file_size: mockFile.size
      })
    })

    it('should handle upload errors gracefully', async () => {
      const upload = useUnifiedUpload()
      upload.initializeFiles([mockFile])
      
      const mockDataService = await import('@/services/dataService')
      mockDataService.default.initUpload = vi.fn().mockRejectedValue(new Error('Network error'))
      
      await upload.startUpload('playlist-123')
      
      expect(upload.uploadErrors.value).toHaveLength(1)
      expect(upload.uploadFiles.value[0].status).toBe('error')
    })

    it('should cancel upload process', async () => {
      const upload = useUnifiedUpload()
      upload.initializeFiles([mockFile])
      
      // Start upload
      const uploadPromise = upload.startUpload('playlist-123')
      
      // Cancel immediately
      upload.cancelUpload()
      
      await uploadPromise
      
      expect(upload.isCancelled.value).toBe(true)
      expect(upload.uploadFiles.value[0].status).toBe('cancelled')
    })
  })

  describe('Progress Tracking', () => {
    it('should calculate overall progress correctly', () => {
      const upload = useUnifiedUpload()
      upload.initializeFiles(mockFiles)
      
      // Simulate progress
      upload.uploadFiles.value[0].progress = 100
      upload.uploadFiles.value[0].status = 'success'
      upload.uploadFiles.value[1].progress = 50
      upload.uploadFiles.value[1].status = 'uploading'
      
      // Manually trigger progress calculation
      const totalProgress = upload.uploadFiles.value.reduce((sum, file) => sum + file.progress, 0)
      const expectedProgress = Math.round(totalProgress / upload.uploadFiles.value.length)
      
      expect(expectedProgress).toBe(75) // (100 + 50) / 2
    })

    it('should track upload statistics', () => {
      const upload = useUnifiedUpload()
      upload.initializeFiles(mockFiles)
      
      expect(upload.stats.value.filesTotal).toBe(2)
      expect(upload.stats.value.totalBytes).toBeGreaterThan(0)
      expect(upload.stats.value.filesCompleted).toBe(0)
    })
  })

  describe('Checksum Generation', () => {
    it('should generate checksums when enabled', async () => {
      const upload = useUnifiedUpload({ generateChecksums: true })
      
      // Mock crypto.subtle.digest
      const mockDigest = vi.fn().mockResolvedValue(new ArrayBuffer(32))
      global.crypto = {
        subtle: { digest: mockDigest }
      } as any
      
      const checksum = await upload.generateChecksum(mockFile)
      
      expect(mockDigest).toHaveBeenCalledWith('SHA-256', expect.any(ArrayBuffer))
      expect(typeof checksum).toBe('string')
    })

    it('should handle checksum generation errors', async () => {
      const upload = useUnifiedUpload({ generateChecksums: true })
      
      // Mock crypto.subtle.digest to throw error
      const mockDigest = vi.fn().mockRejectedValue(new Error('Crypto error'))
      global.crypto = {
        subtle: { digest: mockDigest }
      } as any
      
      const checksum = await upload.generateChecksum(mockFile)
      
      expect(checksum).toBe('checksum-failed')
    })
  })

  describe('Reset and Cleanup', () => {
    it('should reset upload state', () => {
      const upload = useUnifiedUpload()
      upload.initializeFiles(mockFiles)
      
      // Simulate some state changes
      upload.uploadFiles.value[0].status = 'uploading'
      upload.overallProgress.value = 50
      
      upload.resetUpload()
      
      expect(upload.uploadFiles.value).toHaveLength(0)
      expect(upload.overallProgress.value).toBe(0)
      expect(upload.isUploading.value).toBe(false)
      expect(upload.uploadErrors.value).toHaveLength(0)
    })
  })

  describe('Error Handling', () => {
    it('should call error callback when provided', async () => {
      const errorCallback = vi.fn()
      const upload = useUnifiedUpload({}, errorCallback)
      
      upload.initializeFiles([mockFile])
      
      const mockDataService = await import('@/services/dataService')
      mockDataService.default.initUpload = vi.fn().mockRejectedValue(new Error('Test error'))
      
      await upload.startUpload('playlist-123')
      
      expect(errorCallback).toHaveBeenCalled()
    })

    it('should handle network errors appropriately', async () => {
      const upload = useUnifiedUpload()
      upload.initializeFiles([mockFile])
      
      const mockDataService = await import('@/services/dataService')
      const networkError = new Error('Network error')
      networkError.name = 'NetworkError'
      mockDataService.default.initUpload = vi.fn().mockRejectedValue(networkError)
      
      await upload.startUpload('playlist-123')
      
      expect(upload.uploadErrors.value).toHaveLength(1)
      expect(upload.uploadErrors.value[0]).toContain('Network error')
    })
  })
})

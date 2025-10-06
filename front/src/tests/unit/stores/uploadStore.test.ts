/**
 * Unit tests for uploadStore.ts
 *
 * Tests the upload state management store including:
 * - Modal state management
 * - Global upload queue management
 * - Upload operations
 * - Configuration management
 * - History tracking
 * - Integration with useUpload composable
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useUploadStore } from '@/stores/uploadStore'

// Mock the useUpload composable with all required properties
const mockUploadComposable = {
  uploadFiles: { value: [] },
  isUploading: { value: false },
  isCancelled: { value: false },
  uploadErrors: { value: [] },
  hasErrors: { value: false },
  overallProgress: { value: 0 },
  currentFileProgress: { value: 0 },
  currentFileName: { value: null },
  currentChunkIndex: { value: 0 },
  totalChunks: { value: 0 },
  stats: { value: {
    startTime: 0,
    bytesUploaded: 0,
    totalBytes: 0,
    speed: 0,
    filesCompleted: 0,
    filesTotal: 0
  },
  estimatedTimeRemaining: { value: null },
  uploadSpeedFormatted: { value: '0 B/s' },
  completedFiles: { value: 0 },
  failedFiles: { value: 0 },
  uploadConfig: { value: {
    chunkSize: 1024 * 1024,
    maxRetries: 3,
    useChunkedUpload: true,
    validateFiles: true,
    generateChecksums: false
  },
  validateFile: vi.fn((file: File) => null),
  generateChecksum: vi.fn(async (file: File) => 'mock-checksum'),
  initializeFiles: vi.fn(),
  startUpload: vi.fn(),
  cancelUpload: vi.fn(),
  resetUpload: vi.fn()
}

vi.mock('@/composables/useUpload', () => ({
  useUpload: () => mockUploadComposable
}))

describe('uploadStore', () => {
  let store: ReturnType<typeof useUploadStore>
  let pinia: ReturnType<typeof createPinia>

  // Helper to create mock files
  const createMockFile = (name: string, type: string = 'audio/mpeg', size: number = 1024): File => {
    const file = new File(['mock content'], name, { type })
    Object.defineProperty(file, 'size', { value: size, writable: false })
    return file
  }

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
    store = useUploadStore()
    vi.clearAllMocks()

    // Reset upload composable mocks
    mockUploadComposable.isUploading.value = false
    mockUploadComposable.overallProgress.value = 0
    mockUploadComposable.uploadFiles.value = []
    mockUploadComposable.hasErrors.value = false
    mockUploadComposable.completedFiles.value = 0
    mockUploadComposable.failedFiles.value = 0
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('Store Initialization', () => {
    it('should initialize with default state', () => {
      expect(store.globalUploadQueue.size)
        .toBe(0)
      expect(store.uploadHistory)
        .toEqual([])
      expect(store.isModalOpen)
        .toBe(false)
      expect(store.modalPlaylistId)
        .toBe(null)
      expect(store.globalUploadProgress)
        .toBe(0)
    })

    it('should have proper reactive state', () => {
      expect(store.globalUploadQueue instanceof Map)
        .toBe(true)
      expect(Array.isArray(store.uploadHistory))
        .toBe(true)
      expect(typeof store.isModalOpen)
        .toBe('boolean')
    })
  })

  describe('Modal Management', () => {
    it('should open upload modal', () => {
      const playlistId = 'playlist-1'

      store.openUploadModal(playlistId)

      expect(store.isModalOpen)
        .toBe(true)
      expect(store.modalPlaylistId)
        .toBe(playlistId)
    })

    it('should close upload modal', () => {
      store.openUploadModal('playlist-1')

      store.closeUploadModal()

      expect(store.isModalOpen)
        .toBe(false)
      expect(store.modalPlaylistId)
        .toBe(null)
    })
  })

  describe('Upload Queue Management', () => {
    it('should add files to upload queue', () => {
      const files = [
        createMockFile('track1.mp3'),
        createMockFile('track2.wav', 'audio/wav')
      ]
      const playlistId = 'playlist-1'

      // Mock initializeFiles to set up uploadFiles
      mockUploadComposable.initializeFiles.mockImplementation(() => {
        mockUploadComposable.uploadFiles.value = files.map(file => ({
          file,
          status: 'pending' as const,
          progress: 0,
          retryCount: 0
        }))
      })

      store.addFilesToQueue(playlistId, files)

      expect(mockUploadComposable.initializeFiles)
        .toHaveBeenCalledWith(files)
      expect(store.globalUploadQueue.has(playlistId))
        .toBe(true)
      expect(store.globalUploadQueue.get(playlistId))
        .toHaveLength(2)
    })

    it('should remove files from queue', () => {
      const files = [createMockFile('test.mp3')]
      const playlistId = 'playlist-1'

      // Mock initializeFiles to set up uploadFiles
      mockUploadComposable.initializeFiles.mockImplementation(() => {
        mockUploadComposable.uploadFiles.value = files.map(file => ({
          file,
          status: 'pending' as const,
          progress: 0,
          retryCount: 0
        }))
      })

      store.addFilesToQueue(playlistId, files)
      expect(store.globalUploadQueue.get(playlistId))
        .toHaveLength(1)

      store.removeFileFromQueue(playlistId, 0)
      // When all files are removed, the playlist key is deleted from the map
      expect(store.globalUploadQueue.has(playlistId))
        .toBe(false)
    })

    it('should clear entire queue for playlist', () => {
      const files = [
        createMockFile('track1.mp3'),
        createMockFile('track2.mp3')
      ]
      const playlistId = 'playlist-1'

      // Mock initializeFiles to set up uploadFiles
      mockUploadComposable.initializeFiles.mockImplementation(() => {
        mockUploadComposable.uploadFiles.value = files.map(file => ({
          file,
          status: 'pending' as const,
          progress: 0,
          retryCount: 0
        }))
      })

      store.addFilesToQueue(playlistId, files)
      expect(store.globalUploadQueue.get(playlistId))
        .toHaveLength(2)

      store.clearQueue(playlistId)
      expect(store.globalUploadQueue.has(playlistId))
        .toBe(false)
    })

    it('should clear all queues', () => {
      // Mock initializeFiles for both calls
      mockUploadComposable.initializeFiles.mockImplementation(() => {
        mockUploadComposable.uploadFiles.value = [{
          file: createMockFile('test.mp3'),
          status: 'pending' as const,
          progress: 0,
          retryCount: 0
        }]
      })

      store.addFilesToQueue('playlist-1', [createMockFile('track1.mp3')])
      store.addFilesToQueue('playlist-2', [createMockFile('track2.mp3')])

      expect(store.globalUploadQueue.size)
        .toBe(2)

      store.clearQueue()
      expect(store.globalUploadQueue.size)
        .toBe(0)
    })
  })

  describe('Upload Operations', () => {
    it('should start upload for playlist', async () => {
      const files = [createMockFile('track1.mp3')]
      const playlistId = 'playlist-1'

      // Setup files in queue
      mockUploadComposable.initializeFiles.mockImplementation(() => {
        mockUploadComposable.uploadFiles.value = files.map(file => ({
          file,
          status: 'pending' as const,
          progress: 0,
          retryCount: 0
        }))
      })

      store.addFilesToQueue(playlistId, files)

      // Mock successful upload
      mockUploadComposable.startUpload.mockResolvedValue(undefined)
      mockUploadComposable.completedFiles.value = 1

      await store.startUpload(playlistId)

      expect(mockUploadComposable.initializeFiles)
        .toHaveBeenCalledWith(files)
      expect(mockUploadComposable.startUpload)
        .toHaveBeenCalledWith(playlistId)
      expect(store.uploadHistory)
        .toHaveLength(1)
      expect(store.uploadHistory[0].success)
        .toBe(true)
    })

    it('should handle upload failures', async () => {
      const files = [createMockFile('track1.mp3')]
      const playlistId = 'playlist-1'

      // Setup files in queue
      mockUploadComposable.initializeFiles.mockImplementation(() => {
        mockUploadComposable.uploadFiles.value = files.map(file => ({
          file,
          status: 'error' as const,
          progress: 0,
          retryCount: 0
        }))
      })

      store.addFilesToQueue(playlistId, files)

      // Mock failed upload
      const error = new Error('Upload failed')
      mockUploadComposable.startUpload.mockRejectedValue(error)

      await expect(store.startUpload(playlistId)).rejects.toThrow('Upload failed')

      expect(store.uploadHistory)
        .toHaveLength(1)
      expect(store.uploadHistory[0].success)
        .toBe(false)
    })

    it('should cancel upload', () => {
      store.cancelUpload()

      expect(mockUploadComposable.cancelUpload)
        .toHaveBeenCalled()
    })

    it('should reset upload', () => {
      // Add some data to be cleared
      store.addFilesToQueue('playlist-1', [createMockFile('test.mp3')])

      store.resetUpload()

      expect(mockUploadComposable.resetUpload)
        .toHaveBeenCalled()
      expect(store.globalUploadQueue.size)
        .toBe(0)
    })
  })

  describe('Configuration Management', () => {
    it('should update upload config', () => {
      const newConfig = { chunkSize: 2048 }

      store.updateConfig(newConfig)

      expect(mockUploadComposable.uploadConfig.value.chunkSize)
        .toBe(2048)
    })
  })

  describe('History Management', () => {
    it('should clear upload history', () => {
      // Add some history
      store.uploadHistory.push({
        timestamp: Date.now(),
        playlistId: 'playlist-1',
        files: [],
        success: true
      })

      expect(store.uploadHistory)
        .toHaveLength(1)

      store.clearHistory()

      expect(store.uploadHistory)
        .toHaveLength(0)
    })

    it('should get history for specific playlist', () => {
      const history1 = {
        timestamp: Date.now(),
        playlistId: 'playlist-1',
        files: [],
        success: true
      }
      const history2 = {
        timestamp: Date.now(),
        playlistId: 'playlist-2',
        files: [],
        success: true
      }

      store.uploadHistory.push(history1, history2)

      const playlist1History = store.getHistoryForPlaylist('playlist-1')

      expect(playlist1History)
        .toHaveLength(1)
      expect(playlist1History[0])
        .toStrictEqual(history1)
    })
  })

  describe('Computed Properties', () => {
    it('should calculate total pending files', () => {
      // Mock files in queue
      const mockFiles = [
        { file: createMockFile('test1.mp3'), status: 'pending' as const, progress: 0, retryCount: 0 },
        { file: createMockFile('test2.mp3'), status: 'pending' as const, progress: 0, retryCount: 0 },
        { file: createMockFile('test3.mp3'), status: 'success' as const, progress: 100, retryCount: 0 }
      ]

      store.globalUploadQueue.set('playlist-1', mockFiles)

      expect(store.totalPendingFiles)
        .toBe(2)
    })

    it('should calculate global upload progress', () => {
      const mockFiles = [
        { file: createMockFile('test1.mp3'), status: 'success' as const, progress: 100, retryCount: 0 },
        { file: createMockFile('test2.mp3'), status: 'success' as const, progress: 100, retryCount: 0 },
        { file: createMockFile('test3.mp3'), status: 'pending' as const, progress: 0, retryCount: 0 }
      ]

      store.globalUploadQueue.set('playlist-1', mockFiles)

      // Should calculate: 2 success / 3 total = 67%
      expect(store.globalUploadProgress)
        .toBe(67)
    })

    it('should return 0 progress when no files', () => {
      expect(store.globalUploadProgress)
        .toBe(0)
    })

    it('should check for active uploads', () => {
      mockUploadComposable.isUploading.value = true

      expect(store.hasActiveUploads)
        .toBe(true)
    })
  })

  describe('Integration with Composable', () => {
    it('should expose composable properties correctly', () => {
      mockUploadComposable.uploadFiles.value = [
        { file: createMockFile('test.mp3'), status: 'pending', progress: 0, retryCount: 0 }
      ]
      mockUploadComposable.isUploading.value = true
      mockUploadComposable.overallProgress.value = 50

      expect(store.uploadFiles.value)
        .toHaveLength(1)
      expect(store.isUploading.value)
        .toBe(true)
      expect(store.overallProgress.value)
        .toBe(50)
    })

    it('should call composable methods correctly', async () => {
      const file = createMockFile('test.mp3')

      const result = store.validateFile(file)
      expect(mockUploadComposable.validateFile)
        .toHaveBeenCalledWith(file)

      await store.generateChecksum(file)
      expect(mockUploadComposable.generateChecksum)
        .toHaveBeenCalledWith(file)
    })
  })
})
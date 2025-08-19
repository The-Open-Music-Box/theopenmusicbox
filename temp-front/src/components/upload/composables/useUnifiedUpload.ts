/**
 * Unified Upload Composable
 * 
 * Consolidates all upload functionality into a single, robust composable.
 * Supports both chunked and traditional uploads with comprehensive error handling,
 * progress tracking, and state management.
 * 
 * Features:
 * - Chunked upload with configurable chunk size
 * - Real-time progress tracking via Socket.IO
 * - Automatic retry logic with exponential backoff
 * - File validation and checksum generation
 * - Comprehensive error handling and recovery
 * - Memory leak prevention with proper cleanup
 * - Cancellation support
 * - Upload statistics and ETA calculation
 */

import { ref, reactive, computed, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import dataService from '@/services/dataService'
import socketService from '@/services/socketService'
import type { SocketProgressData, SocketCompleteData, SocketErrorData } from '@/types/socket'
import { createTypedSocketHandler } from '@/types/socket'
import { normalizeError, type UploadError } from '@/types/errors'
import { logger } from '@/utils/logger'
import { SOCKET_EVENTS } from '../../../constants/apiRoutes'

// Configuration constants
const DEFAULT_CHUNK_SIZE = 1024 * 1024 // 1MB
const MAX_RETRY_ATTEMPTS = 3
const PROGRESS_THROTTLE_MS = 500
const RETRY_DELAY_BASE = 1000 // Base delay for exponential backoff

// Upload file interface
export interface UploadFile {
  file: File
  status: 'pending' | 'uploading' | 'success' | 'error' | 'cancelled'
  progress: number
  sessionId?: string
  error?: string
  retryCount: number
  checksum?: string
}

// Upload statistics interface
export interface UploadStats {
  startTime: number
  bytesUploaded: number
  totalBytes: number
  speed: number // bytes per second
  filesCompleted: number
  filesTotal: number
}

// Upload configuration interface
export interface UploadConfig {
  chunkSize: number
  maxRetries: number
  useChunkedUpload: boolean
  validateFiles: boolean
  generateChecksums: boolean
}

/**
 * Unified Upload Composable
 * 
 * Provides a complete upload solution with chunked upload support,
 * progress tracking, error handling, and state management.
 */
export function useUnifiedUpload(config: Partial<UploadConfig> = {}, onError?: (error: UploadError) => void) {
  const { t } = useI18n()

  // Merge configuration with defaults
  const uploadConfig = ref<UploadConfig>({
    chunkSize: DEFAULT_CHUNK_SIZE,
    maxRetries: MAX_RETRY_ATTEMPTS,
    useChunkedUpload: true,
    validateFiles: true,
    generateChecksums: true,
    ...config
  })

  // Core state
  const uploadFiles = ref<UploadFile[]>([])
  const currentPlaylistId = ref<string | null>(null)
  const currentFileIndex = ref<number>(0)
  const isUploading = ref<boolean>(false)
  const isCancelled = ref<boolean>(false)
  const isCleanupInProgress = ref<boolean>(false)
  const uploadErrors = ref<string[]>([])

  // Progress state
  const overallProgress = ref<number>(0)
  const currentFileProgress = ref<number>(0)
  const currentFileName = ref<string | null>(null)
  const currentChunkIndex = ref<number>(0)
  const totalChunks = ref<number>(0)

  // Statistics
  const stats = ref<UploadStats>({
    startTime: 0,
    bytesUploaded: 0,
    totalBytes: 0,
    speed: 0,
    filesCompleted: 0,
    filesTotal: 0
  })

  // Socket cleanup functions
  const socketCleanupFunctions = ref<(() => void)[]>([])

  // Progress throttling
  const lastProgressUpdate = ref<number>(0)
  const progressUpdateQueue = ref<Map<string, number>>(new Map())

  // Computed properties
  const estimatedTimeRemaining = computed(() => {
    if (stats.value.speed === 0 || stats.value.bytesUploaded === 0) return null
    const remainingBytes = stats.value.totalBytes - stats.value.bytesUploaded
    return Math.ceil(remainingBytes / stats.value.speed)
  })

  const uploadSpeedFormatted = computed(() => {
    const speed = stats.value.speed
    if (speed < 1024) return `${speed.toFixed(0)} B/s`
    if (speed < 1024 * 1024) return `${(speed / 1024).toFixed(1)} KB/s`
    return `${(speed / (1024 * 1024)).toFixed(1)} MB/s`
  })

  const hasErrors = computed(() => uploadErrors.value.length > 0)

  const completedFiles = computed(() => 
    uploadFiles.value.filter(f => f.status === 'success').length
  )

  const failedFiles = computed(() => 
    uploadFiles.value.filter(f => f.status === 'error').length
  )

  // Utility functions
  const generateChecksum = async (file: File | Blob): Promise<string> => {
    try {
      const buffer = await file.arrayBuffer()
      const hashBuffer = await crypto.subtle.digest('SHA-256', buffer)
      return Array.from(new Uint8Array(hashBuffer))
        .map(b => b.toString(16).padStart(2, '0'))
        .join('')
    } catch (error) {
      console.warn('Failed to generate checksum:', error)
      return 'checksum-failed'
    }
  }

  const validateFile = (file: File): string | null => {
    if (!uploadConfig.value.validateFiles) return null

    // Check file type
    if (!file.type.startsWith('audio/')) {
      return t('upload.invalidFileType', { filename: file.name })
    }

    // Check file size (max 100MB)
    const maxSize = 100 * 1024 * 1024
    if (file.size > maxSize) {
      return t('upload.fileTooLarge', { filename: file.name, maxSize: '100MB' })
    }

    // Check file name
    if (file.name.length > 255) {
      return t('upload.filenameTooLong', { filename: file.name })
    }

    return null
  }

  const sliceFile = (file: File, chunkIndex: number): Blob => {
    const start = chunkIndex * uploadConfig.value.chunkSize
    const end = Math.min(start + uploadConfig.value.chunkSize, file.size)
    return file.slice(start, end)
  }

  const calculateExponentialBackoff = (retryCount: number): number => {
    return RETRY_DELAY_BASE * Math.pow(2, retryCount)
  }

  // Error handling
  const handleError = (error: unknown, context: string, filename?: string) => {
    const normalizedError = normalizeError(error, context) as UploadError
    normalizedError.fileName = filename
    
    logger.error(`Upload error in ${context}`, { error: normalizedError }, 'UnifiedUpload')
    
    const errorMessage = filename 
      ? `${t('upload.failedToUpload')} ${filename}: ${normalizedError.message}`
      : `${t('upload.error')}: ${normalizedError.message}`
    
    uploadErrors.value.push(errorMessage)
    isUploading.value = false
    
    // Emit error event for parent components
    if (onError) {
      onError(normalizedError)
    }
  }

  // Socket.IO management
  const setupSocketListeners = () => {
    cleanupSocketListeners()

    const progressHandler = (data: SocketProgressData) => {
      const currentFile = uploadFiles.value[currentFileIndex.value]
      if (currentFile && data.session_id === currentFile.sessionId) {
        // Queue progress updates to avoid UI blocking
        progressUpdateQueue.value.set(data.session_id, data.progress || 0)
        
        // Throttle progress updates
        const now = Date.now()
        if (now - lastProgressUpdate.value > PROGRESS_THROTTLE_MS) {
          // Process queued updates
          progressUpdateQueue.value.forEach((progress, sessionId) => {
            const file = uploadFiles.value.find(f => f.sessionId === sessionId)
            if (file) {
              file.progress = Math.round(progress)
            }
          })
          
          // Update total progress
          const totalProgress = uploadFiles.value.reduce((sum, file) => {
            return sum + (file.progress || 0)
          }, 0)
          
          overallProgress.value = Math.round(totalProgress / uploadFiles.value.length)
          lastProgressUpdate.value = now
          progressUpdateQueue.value.clear()
        }
      }
    }

    const completeHandler = (data: SocketCompleteData) => {
      const currentFile = uploadFiles.value[currentFileIndex.value]
      if (currentFile && data.session_id === currentFile.sessionId) {
        currentFile.status = 'success'
        currentFile.progress = 100
        
        // File completion is handled by the main upload loop
        logger.debug('Upload completed via socket', { sessionId: data.session_id, fileName: currentFile.file.name }, 'UnifiedUpload')
      }
    }

    const errorHandler = (data: SocketErrorData) => {
      const currentFile = uploadFiles.value[currentFileIndex.value]
      if (currentFile && data.session_id === currentFile.sessionId) {
        currentFile.status = 'error'
        const error: UploadError = {
          message: data.error || 'Socket upload error',
          code: data.code,
          context: data.context || 'Socket error event',
          sessionId: data.session_id,
          fileName: currentFile.file.name
        }
        handleError(error, 'Socket error event', currentFile.file.name)
      }
    }

    // Register listeners with type safety
    socketService.on(SOCKET_EVENTS.UPLOAD_PROGRESS, createTypedSocketHandler<SocketProgressData>(progressHandler))
    socketService.on(SOCKET_EVENTS.UPLOAD_COMPLETE, createTypedSocketHandler<SocketCompleteData>(completeHandler))
    socketService.on(SOCKET_EVENTS.UPLOAD_ERROR, createTypedSocketHandler<SocketErrorData>(errorHandler))

    // Store cleanup functions
    socketCleanupFunctions.value = [
      () => socketService.off(SOCKET_EVENTS.UPLOAD_PROGRESS),
      () => socketService.off(SOCKET_EVENTS.UPLOAD_COMPLETE),
      () => socketService.off(SOCKET_EVENTS.UPLOAD_ERROR)
    ]
  }

  const cleanupSocketListeners = () => {
    socketCleanupFunctions.value.forEach(cleanup => cleanup())
    socketCleanupFunctions.value = []
  }

  // Progress calculation
  const updateOverallProgress = () => {
    if (uploadFiles.value.length === 0) {
      overallProgress.value = 0
      return
    }

    const totalFiles = uploadFiles.value.length
    const completedFiles = uploadFiles.value.filter(f => f.status === 'success').length
    const currentProgress = currentFileProgress.value / 100

    overallProgress.value = Math.round(((completedFiles + currentProgress) / totalFiles) * 100)
  }

  const updateStats = (bytesUploaded: number) => {
    stats.value.bytesUploaded += bytesUploaded
    
    const elapsedTime = (Date.now() - stats.value.startTime) / 1000
    if (elapsedTime > 0) {
      stats.value.speed = stats.value.bytesUploaded / elapsedTime
    }
  }

  // Upload methods
  const uploadChunkWithRetry = async (
    playlistId: string,
    formData: FormData,
    chunkIndex: number,
    uploadFile: UploadFile
  ): Promise<boolean> => {
    let lastError: Error | null = null

    for (let attempt = 0; attempt <= uploadConfig.value.maxRetries; attempt++) {
      if (isCancelled.value) return false

      try {
        await dataService.uploadChunk(playlistId, uploadFile.sessionId!, chunkIndex, formData)
        return true
      } catch (error) {
        lastError = error as Error
        uploadFile.retryCount++

        if (attempt < uploadConfig.value.maxRetries) {
          const delay = calculateExponentialBackoff(attempt)
          console.warn(`[UnifiedUpload] Chunk ${chunkIndex} failed, retrying in ${delay}ms (attempt ${attempt + 1}/${uploadConfig.value.maxRetries + 1})`)
          await new Promise(resolve => setTimeout(resolve, delay))
        }
      }
    }

    throw lastError || new Error('Upload failed after retries')
  }

  const uploadFileChunked = async (uploadFile: UploadFile): Promise<void> => {
    const { file } = uploadFile
    currentFileName.value = file.name
    currentFileProgress.value = 0
    currentChunkIndex.value = 0

    // Calculate total chunks
    const totalFileChunks = Math.ceil(file.size / uploadConfig.value.chunkSize)
    totalChunks.value = totalFileChunks

    try {
      // 1. Initialize upload session
      const metadata = {
        filename: file.name,
        file_size: file.size
      }

      const initResponse = await dataService.initUpload(currentPlaylistId.value!, metadata)
      uploadFile.sessionId = initResponse.session_id

      // 2. Upload chunks
      for (let i = 0; i < totalFileChunks; i++) {
        if (isCancelled.value) break

        const chunk = sliceFile(file, i)
        const formData = new FormData()
        
        if (!uploadFile.sessionId) {
          throw new Error('Session ID is required for chunk upload')
        }
        
        formData.append('session_id', uploadFile.sessionId)
        formData.append('chunk_index', i.toString())
        formData.append('file', new File([chunk], file.name, { type: file.type }))

        // Add checksum if enabled
        if (uploadConfig.value.generateChecksums) {
          const chunkChecksum = await generateChecksum(chunk)
          if (chunkChecksum && chunkChecksum !== 'checksum-failed') {
            formData.append('checksum', chunkChecksum)
          }
        }

        await uploadChunkWithRetry(currentPlaylistId.value!, formData, i, uploadFile)
        
        currentChunkIndex.value = i + 1
        currentFileProgress.value = Math.round(((i + 1) / totalFileChunks) * 100)
        uploadFile.progress = currentFileProgress.value

        // Update statistics
        updateStats(chunk.size)
        updateOverallProgress()
      }

      // 3. Finalize upload
      if (!isCancelled.value && uploadFile.sessionId) {
        await dataService.finalizeUpload(currentPlaylistId.value!, {
          session_id: uploadFile.sessionId
        })
        
        uploadFile.status = 'success'
        uploadFile.progress = 100
        stats.value.filesCompleted++
      }

    } catch (error) {
      uploadFile.status = 'error'
      uploadFile.error = error instanceof Error ? error.message : 'Upload failed'
      handleError(error, 'Chunked upload', file.name)
      throw error
    }
  }

  const uploadFileTraditional = async (uploadFile: UploadFile): Promise<void> => {
    const { file } = uploadFile
    currentFileName.value = file.name
    currentFileProgress.value = 0

    try {
      await dataService.uploadFiles(currentPlaylistId.value!, [file], (progressEvent) => {
        if (progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          currentFileProgress.value = progress
          uploadFile.progress = progress
          updateOverallProgress()
        }
      })

      uploadFile.status = 'success'
      uploadFile.progress = 100
      stats.value.filesCompleted++
      updateStats(file.size)

    } catch (error) {
      uploadFile.status = 'error'
      uploadFile.error = error instanceof Error ? error.message : 'Upload failed'
      handleError(error, 'Traditional upload', file.name)
      throw error
    }
  }

  // Public methods
  const initializeFiles = (files: File[]) => {
    // Validate files
    const validationErrors: string[] = []
    const validFiles: File[] = []

    for (const file of files) {
      const error = validateFile(file)
      if (error) {
        validationErrors.push(error)
      } else {
        validFiles.push(file)
      }
    }

    // Update errors
    uploadErrors.value = validationErrors

    // Initialize upload files
    uploadFiles.value = validFiles.map(file => ({
      file,
      status: 'pending',
      progress: 0,
      retryCount: 0
    }))

    // Initialize statistics
    stats.value = {
      startTime: 0,
      bytesUploaded: 0,
      totalBytes: validFiles.reduce((total, file) => total + file.size, 0),
      speed: 0,
      filesCompleted: 0,
      filesTotal: validFiles.length
    }

    // Reset progress
    overallProgress.value = 0
    currentFileProgress.value = 0
    currentFileIndex.value = 0
    currentFileName.value = null
  }

  const startUpload = async (playlistId: string): Promise<void> => {
    if (isUploading.value || uploadFiles.value.length === 0) {
      return
    }

    try {
      isUploading.value = true
      isCancelled.value = false
      currentPlaylistId.value = playlistId
      stats.value.startTime = Date.now()
      uploadErrors.value = []

      // Setup socket listeners
      setupSocketListeners()

      // Upload files sequentially
      for (let i = 0; i < uploadFiles.value.length; i++) {
        if (isCancelled.value) break

        currentFileIndex.value = i
        const uploadFile = uploadFiles.value[i]
        uploadFile.status = 'uploading'

        try {
          if (uploadConfig.value.useChunkedUpload) {
            await uploadFileChunked(uploadFile)
          } else {
            await uploadFileTraditional(uploadFile)
          }

          // Small delay between files
          if (i < uploadFiles.value.length - 1) {
            await new Promise(resolve => setTimeout(resolve, 200))
          }

        } catch (error: unknown) {
          const normalizedError = normalizeError(error, 'FileUpload')
          logger.error(`File ${i + 1} upload failed`, { error: normalizedError, fileName: uploadFile.file.name }, 'UnifiedUpload')
          uploadFile.status = 'error'
          // Continue with next file
        }
      }

    } finally {
      isUploading.value = false
      currentFileName.value = null
      cleanupSocketListeners()
    }
  }

  const cancelUpload = () => {
    isCancelled.value = true
    isUploading.value = false
    
    // Mark uploading files as cancelled
    uploadFiles.value.forEach(file => {
      if (file.status === 'uploading') {
        file.status = 'cancelled'
        file.error = 'Cancelled by user'
      }
    })

    performCleanup()
  }

  const resetUpload = () => {
    uploadFiles.value = []
    uploadErrors.value = []
    currentFileIndex.value = 0
    currentFileName.value = null
    overallProgress.value = 0
    currentFileProgress.value = 0
    isUploading.value = false
    isCancelled.value = false
    
    stats.value = {
      startTime: 0,
      bytesUploaded: 0,
      totalBytes: 0,
      speed: 0,
      filesCompleted: 0,
      filesTotal: 0
    }

    performCleanup()
  }

  const performCleanup = () => {
    if (isCleanupInProgress.value) return

    isCleanupInProgress.value = true

    try {
      cleanupSocketListeners()
      currentPlaylistId.value = null
      progressUpdateQueue.value.clear()
      
      // Clear any pending timers or intervals
      if (typeof window !== 'undefined') {
        // Clear any RAF callbacks that might be pending
        const highestTimeoutId = setTimeout(() => { /* cleanup timers */ }, 0) as unknown as number
        for (let i = 0; i < highestTimeoutId; i++) {
          clearTimeout(i)
        }
      }
    } catch (error) {
      console.warn('[UnifiedUpload] Error during cleanup:', error)
    } finally {
      isCleanupInProgress.value = false
    }
  }

  // Lifecycle
  onUnmounted(() => {
    performCleanup()
  })

  return {
    // Configuration
    uploadConfig,

    // State
    uploadFiles,
    isUploading,
    isCancelled,
    uploadErrors,
    hasErrors,

    // Progress
    overallProgress,
    currentFileProgress,
    currentFileName,
    currentChunkIndex,
    totalChunks,

    // Statistics
    stats,
    estimatedTimeRemaining,
    uploadSpeedFormatted,
    completedFiles,
    failedFiles,

    // Methods
    initializeFiles,
    startUpload,
    cancelUpload,
    resetUpload,

    // Utilities
    validateFile,
    generateChecksum
  }
}

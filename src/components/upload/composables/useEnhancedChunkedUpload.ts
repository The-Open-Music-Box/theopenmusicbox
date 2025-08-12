/**
 * Enhanced Chunked Upload Composable
 *
 * An improved version of the chunked upload that includes:
 * - Better error handling to prevent page refreshes
 * - Robust state management
 * - Cleanup mechanisms to prevent memory leaks
 * - Defensive programming against async errors
 */

import { ref, computed, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import dataService from '../../../services/dataService'
import socketService from '../../../services/realSocketService'
import { SOCKET_EVENTS } from '../../../constants/apiRoutes'

const CHUNK_SIZE = 1024 * 1024 // 1MB chunks
const MAX_RETRY_ATTEMPTS = 3

export function useEnhancedChunkedUpload() {
  const { t } = useI18n()

  // State management
  const uploadFiles = ref<File[]>([])
  const currentPlaylistId = ref<string | null>(null)
  const currentSessionId = ref<string | null>(null)
  const currentFileIndex = ref<number>(0)
  const totalChunks = ref<number>(0)
  const currentChunkIndex = ref<number>(0)
  const uploadProgress = ref<number>(0)
  const uploadState = ref<'idle' | 'initializing' | 'uploading' | 'completing' | 'error' | 'cancelled'>('idle')
  const isUploading = ref<boolean>(false)
  const isCleanupInProgress = ref<boolean>(false)
  const isUploadingFile = ref<boolean>(false)
  const currentFileName = ref<string | null>(null)
  const uploadErrors = ref<string[]>([])

  // Statistics
  const stats = ref({
    startTime: 0,
    bytesUploaded: 0,
    totalBytes: 0,
    speed: 0
  })

  // Socket event cleanup functions
  const socketCleanupFunctions = ref<(() => void)[]>([])

  // Computed properties
  const estimatedTimeRemaining = computed(() => {
    if (stats.value.speed === 0 || stats.value.bytesUploaded === 0) return null
    const remainingBytes = stats.value.totalBytes - stats.value.bytesUploaded
    return Math.ceil(remainingBytes / stats.value.speed)
  })

  const currentProgressPercent = computed(() => {
    if (totalChunks.value === 0) return 0
    return Math.round((currentChunkIndex.value / totalChunks.value) * 100)
  })

  // Enhanced error handler
  const handleError = (error: any, context: string) => {
    console.error(`🚨 [EnhancedChunkedUpload] Error in ${context}:`, error)

    // Add to error list with context
    const errorMessage = `${context}: ${error.message || 'Unknown error'}`
    if (!uploadErrors.value.includes(errorMessage)) {
      uploadErrors.value.push(errorMessage)
    }

    // Update state
    uploadState.value = 'error'
    isUploading.value = false

    // Cleanup resources
    performCleanup()
  }

  // Safe async wrapper
  const safeAsync = async <T>(
    operation: () => Promise<T>,
    context: string,
    fallback: T
  ): Promise<T> => {
    try {
      return await operation()
    } catch (error) {
      handleError(error, context)
      return fallback
    }
  }

  // Enhanced socket listener setup
  const setupSocketListeners = () => {
    // Clean up existing listeners first
    cleanupSocketListeners()

    try {
      const progressHandler = (data: any) => {
        if (data.session_id === currentSessionId.value) {
          uploadProgress.value = data.progress
          currentChunkIndex.value = data.chunk_index + 1
        }
      }

      const completeHandler = (data: any) => {
        if (data.session_id === currentSessionId.value) {
          uploadProgress.value = 100
          console.log('[Enhanced Upload] Socket.IO upload complete received, but file progression is handled directly after finalization')
        }
      }

      const errorHandler = (data: any) => {
        if (data.session_id === currentSessionId.value) {
          handleError(new Error(data.error || 'Socket upload error'), 'Socket error event')
        }
      }

      // Register listeners
      socketService.on(SOCKET_EVENTS.UPLOAD_PROGRESS, progressHandler)
      socketService.on(SOCKET_EVENTS.UPLOAD_COMPLETE, completeHandler)
      socketService.on(SOCKET_EVENTS.UPLOAD_ERROR, errorHandler)

      // Store cleanup functions
      socketCleanupFunctions.value = [
        () => socketService.off(SOCKET_EVENTS.UPLOAD_PROGRESS),
        () => socketService.off(SOCKET_EVENTS.UPLOAD_COMPLETE),
        () => socketService.off(SOCKET_EVENTS.UPLOAD_ERROR)
      ]
    } catch (error) {
      handleError(error, 'Socket listener setup')
    }
  }

  // Enhanced socket cleanup
  const cleanupSocketListeners = () => {
    try {
      socketCleanupFunctions.value.forEach(cleanup => {
        try {
          cleanup()
        } catch (error) {
          console.warn('Error during socket cleanup:', error)
        }
      })
      socketCleanupFunctions.value = []
    } catch (error) {
      console.warn('Error during socket listeners cleanup:', error)
    }
  }

  // File slicing with error handling
  const sliceFile = (file: File, chunkIndex: number): Blob | null => {
    try {
      const start = chunkIndex * CHUNK_SIZE
      const end = Math.min(start + CHUNK_SIZE, file.size)
      return file.slice(start, end)
    } catch (error) {
      handleError(error, 'File slicing')
      return null
    }
  }

  // Checksum generation with crypto API fallback
  const generateChecksum = async (file: File | Blob): Promise<string | null> => {
    // Check if crypto.subtle is available (not available on older browsers or some mobile browsers)
    if (!window.crypto || !window.crypto.subtle) {
      console.warn('[Enhanced Upload] crypto.subtle not available, skipping checksum')
      return null // Return null to skip checksum validation
    }

    return safeAsync(async () => {
      const buffer = await file.arrayBuffer()
      const hashBuffer = await crypto.subtle.digest('SHA-256', buffer)
      return Array.from(new Uint8Array(hashBuffer))
        .map(b => b.toString(16).padStart(2, '0'))
        .join('')
    }, 'Checksum generation', null)
  }

  // Enhanced chunk upload with retry
  const uploadChunkWithRetry = async (
    playlistId: string,
    formData: FormData,
    chunkIndex: number,
    retryCount = 0
  ): Promise<boolean> => {
    // Defensive check - ensure playlistId is valid
    if (!playlistId || playlistId === 'null' || playlistId === 'undefined') {
      console.error(`[Enhanced Upload] Invalid playlistId: "${playlistId}" for chunk ${chunkIndex}`)
      throw new Error(`Invalid playlistId: "${playlistId}"`)
    }

    return safeAsync(async () => {
      try {
        console.log(`[Enhanced Upload] Uploading chunk ${chunkIndex} to playlist ${playlistId}`)
        await dataService.uploadChunk(playlistId, formData)
        return true
      } catch (error: any) {
        console.warn(`Upload chunk ${chunkIndex} failed (attempt ${retryCount + 1}/${MAX_RETRY_ATTEMPTS}):`, error)

        if (retryCount >= MAX_RETRY_ATTEMPTS - 1) {
          throw error
        }

        // Exponential backoff
        const delayMs = Math.min(1000 * Math.pow(2, retryCount), 10000)
        await new Promise(resolve => setTimeout(resolve, delayMs))

        return uploadChunkWithRetry(playlistId, formData, chunkIndex, retryCount + 1)
      }
    }, `Chunk upload retry (${retryCount + 1})`, false)
  }

  // Enhanced file upload
  const uploadNextFile = async (): Promise<void> => {
    if (uploadState.value === 'cancelled' || uploadState.value === 'error') {
      return
    }

    // Mutex to prevent parallel file uploads
    if (isUploadingFile.value) {
      console.log(`[Enhanced Upload] Skipping uploadNextFile - file upload already in progress`)
      return
    }

    if (!currentPlaylistId.value || currentFileIndex.value >= uploadFiles.value.length) {
      await completeUpload()
      return
    }

    // Acquire mutex
    isUploadingFile.value = true

    const file = uploadFiles.value[currentFileIndex.value]
    currentFileName.value = file.name
    const totalFileChunks = Math.ceil(file.size / CHUNK_SIZE)
    totalChunks.value = totalFileChunks
    uploadState.value = 'uploading'

    await safeAsync(async () => {
      // Initialize session for this file
      console.log(`[Enhanced Upload] Starting file upload with playlistId: ${currentPlaylistId.value}`)

      // Initialize upload session
      const initResponse = await dataService.initUpload(currentPlaylistId.value!, {
        filename: file.name,
        total_size: file.size,
        total_chunks: totalFileChunks
      })

      currentSessionId.value = initResponse.session_id
      console.log(`[Enhanced Upload] Session initialized: ${currentSessionId.value}, playlistId: ${currentPlaylistId.value}`)

      currentChunkIndex.value = 0

      // Upload chunks
      for (let i = 0; i < totalFileChunks; i++) {
        if (uploadState.value === 'cancelled' || uploadState.value === 'error') {
          break
        }

        const chunk = sliceFile(file, i)
        if (!chunk) {
          throw new Error(`Failed to slice chunk ${i}`)
        }

        const formData = new FormData()
        formData.append('session_id', currentSessionId.value!)
        formData.append('chunk_index', i.toString())

        const chunkFile = new File([chunk], file.name, { type: file.type })
        formData.append('file', chunkFile)

        const chunkChecksum = await generateChecksum(new Blob([chunk]))
        if (chunkChecksum !== null) {
          formData.append('checksum', chunkChecksum)
        }

        // Ensure playlistId is still available
        if (!currentPlaylistId.value) {
          throw new Error(`PlaylistId lost during upload at chunk ${i}`)
        }

        const success = await uploadChunkWithRetry(currentPlaylistId.value, formData, i)
        if (!success) {
          throw new Error(`Failed to upload chunk ${i}`)
        }

        currentChunkIndex.value = i + 1

        // Update statistics
        stats.value.bytesUploaded += chunk.size
        const elapsedTime = (Date.now() - stats.value.startTime) / 1000
        if (elapsedTime > 0) {
          stats.value.speed = stats.value.bytesUploaded / elapsedTime
        }

        uploadProgress.value = Math.round((i + 1) / totalFileChunks * 100)
      }

      // Finalize upload
      if (uploadState.value === 'uploading') {
        await dataService.finalizeUpload(currentPlaylistId.value!, {
          session_id: currentSessionId.value!
        })

        // After finalizing, proceed to next file immediately
        // Don't wait for Socket.IO events which may not come
        currentFileIndex.value++

        // Release mutex before proceeding
        isUploadingFile.value = false

        if (currentFileIndex.value >= uploadFiles.value.length) {
          // All files uploaded, complete the process
          await completeUpload()
        } else {
          // Upload next file
          console.log(`[Enhanced Upload] Proceeding to file ${currentFileIndex.value + 1}/${uploadFiles.value.length}`)
          await uploadNextFile()
        }
      }
    }, `Upload file ${file.name}`, undefined)

    // Always release mutex after upload attempt
    isUploadingFile.value = false
  }

  // Complete upload process
  const completeUpload = async (): Promise<void> => {
    uploadState.value = 'completing'

    await safeAsync(async () => {
      uploadState.value = 'idle'
      isUploading.value = false
      uploadFiles.value = []
      currentFileName.value = null
      uploadProgress.value = 100

      // Clean up resources
      performCleanup()
    }, 'Upload completion', undefined)
  }

  // Enhanced upload starter
  const upload = async (playlistIdParam: string): Promise<void> => {
    if (isUploading.value || uploadState.value !== 'idle') {
      console.warn('Upload already in progress, ignoring request')
      return
    }

    await safeAsync(async () => {
      uploadState.value = 'initializing'
      currentPlaylistId.value = playlistIdParam
      isUploading.value = true
      uploadProgress.value = 0
      uploadErrors.value = []
      currentFileIndex.value = 0

      // Initialize statistics
      stats.value = {
        startTime: Date.now(),
        bytesUploaded: 0,
        totalBytes: uploadFiles.value.reduce((total, file) => total + file.size, 0),
        speed: 0
      }

      // Setup socket listeners
      setupSocketListeners()

      // Start upload
      await uploadNextFile()
    }, 'Upload initialization', undefined)
  }

  // Enhanced cancel function
  const cancelUpload = (): void => {
    uploadState.value = 'cancelled'
    isUploading.value = false
    performCleanup()
  }

  // Comprehensive cleanup
  const performCleanup = (): void => {
    if (isCleanupInProgress.value) return

    isCleanupInProgress.value = true

    try {
      // Reset state
      uploadFiles.value = []
      currentSessionId.value = null
      currentFileName.value = null
      currentPlaylistId.value = null
      isUploadingFile.value = false // Release mutex

      // Cleanup socket listeners
      cleanupSocketListeners()

      // Reset upload state
      if (uploadState.value !== 'idle') {
        uploadState.value = 'idle'
      }
    } catch (error) {
      console.warn('Error during cleanup:', error)
    } finally {
      isCleanupInProgress.value = false
    }
  }

  // Cleanup on component unmount
  onUnmounted(() => {
    performCleanup()
  })

  return {
    // State
    uploadFiles,
    uploadProgress,
    isUploading,
    uploadErrors,
    uploadState,
    currentFileName,

    // Computed
    estimatedTimeRemaining,
    currentProgressPercent,

    // Methods
    upload,
    cancelUpload,

    // Enhanced error handling
    handleError,
    safeAsync
  }
}

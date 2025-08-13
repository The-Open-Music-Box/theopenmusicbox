import { ref, reactive, readonly } from 'vue'
import dataService from '@/services/dataService'
import socketService from '@/services/socketService'

export interface UploadFile {
  file: File
  status: 'pending' | 'uploading' | 'success' | 'error'
  progress: number
  sessionId?: string
  error?: string
}

export interface UploadError {
  filename: string
  message: string
}

/**
 * Robust upload composable with simplified, sequential processing
 * Eliminates concurrency issues by processing one file at a time
 */
export function useRobustUpload() {
  // State
  const isUploading = ref(false)
  const uploadFiles = ref<UploadFile[]>([])
  const currentFileIndex = ref(-1)
  const currentFile = ref<File | null>(null)
  const currentFileProgress = ref(0)
  const errors = ref<UploadError[]>([])
  const uploadedSessions = ref<string[]>([])
  const isCancelled = ref(false)
  
  // Progress tracking
  const totalProgress = ref(0)
  const startTime = ref(0)
  const lastProgressTime = ref(0)
  const uploadSpeed = ref(0)
  const estimatedTimeRemaining = ref(0)

  /**
   * Initialize upload files
   */
  function initializeFiles(files: File[]) {
    uploadFiles.value = files.map(file => ({
      file,
      status: 'pending',
      progress: 0
    }))
    errors.value = []
    uploadedSessions.value = []
    currentFileIndex.value = -1
    currentFile.value = null
    currentFileProgress.value = 0
    totalProgress.value = 0
    isCancelled.value = false
  }

  /**
   * Calculate overall progress
   */
  function updateTotalProgress() {
    if (uploadFiles.value.length === 0) {
      totalProgress.value = 0
      return
    }

    const totalFiles = uploadFiles.value.length
    const completedFiles = uploadFiles.value.filter(f => f.status === 'success').length
    const currentProgress = currentFileProgress.value / 100
    
    totalProgress.value = Math.round(((completedFiles + currentProgress) / totalFiles) * 100)
  }

  /**
   * Setup Socket.IO listeners for upload progress
   */
  function setupSocketListeners() {
    socketService.on('upload_progress', (data: any) => {
      if (data.session_id && uploadedSessions.value.includes(data.session_id)) {
        currentFileProgress.value = Math.round(data.progress || 0)
        updateTotalProgress()
        
        // Calculate upload speed and ETA
        const now = Date.now()
        const elapsed = (now - startTime.value) / 1000 // seconds
        const bytesUploaded = data.bytes_uploaded || 0
        
        if (elapsed > 0 && bytesUploaded > 0) {
          uploadSpeed.value = bytesUploaded / elapsed // bytes per second
          
          const totalBytes = uploadFiles.value.reduce((sum, f) => sum + f.file.size, 0)
          const remainingBytes = totalBytes - bytesUploaded
          estimatedTimeRemaining.value = remainingBytes / uploadSpeed.value
        }
      }
    })

    socketService.on('upload_complete', (data: any) => {
      if (data.session_id && uploadedSessions.value.includes(data.session_id)) {
        const fileIndex = uploadFiles.value.findIndex(f => f.sessionId === data.session_id)
        if (fileIndex >= 0) {
          uploadFiles.value[fileIndex].status = 'success'
          uploadFiles.value[fileIndex].progress = 100
          updateTotalProgress()
        }
      }
    })

    socketService.on('upload_error', (data: any) => {
      if (data.session_id && uploadedSessions.value.includes(data.session_id)) {
        const fileIndex = uploadFiles.value.findIndex(f => f.sessionId === data.session_id)
        if (fileIndex >= 0) {
          uploadFiles.value[fileIndex].status = 'error'
          uploadFiles.value[fileIndex].error = data.error || 'Upload failed'
          errors.value.push({
            filename: uploadFiles.value[fileIndex].file.name,
            message: data.error || 'Upload failed'
          })
        }
      }
    })
  }

  /**
   * Cleanup Socket.IO listeners
   */
  function cleanupSocketListeners() {
    socketService.off('upload_progress')
    socketService.off('upload_complete')
    socketService.off('upload_error')
  }

  /**
   * Upload a single file with robust error handling
   */
  async function uploadSingleFile(playlistId: string, uploadFile: UploadFile): Promise<void> {
    const file = uploadFile.file
    const chunkSize = 1024 * 1024 // 1MB chunks
    const totalChunks = Math.ceil(file.size / chunkSize)
    
    console.log(`[RobustUpload] Starting upload: ${file.name} (${file.size} bytes, ${totalChunks} chunks)`)
    
    try {
      // Step 1: Initialize upload session
      const initResponse = await dataService.initUpload(playlistId, {
        filename: file.name,
        total_chunks: totalChunks,
        total_size: file.size
      })
      
      if (!initResponse.session_id) {
        throw new Error('No session ID received from server')
      }
      
      const sessionId = initResponse.session_id
      uploadFile.sessionId = sessionId
      uploadedSessions.value.push(sessionId)
      
      console.log(`[RobustUpload] Session created: ${sessionId}`)
      
      // Step 2: Upload chunks sequentially
      for (let chunkIndex = 0; chunkIndex < totalChunks; chunkIndex++) {
        if (isCancelled.value) {
          throw new Error('Upload cancelled by user')
        }
        
        const start = chunkIndex * chunkSize
        const end = Math.min(start + chunkSize, file.size)
        const chunk = file.slice(start, end)
        
        const formData = new FormData()
        formData.append('session_id', sessionId)
        formData.append('chunk_index', chunkIndex.toString())
        formData.append('file', chunk)
        
        await dataService.uploadChunk(playlistId, formData)
        
        // Update progress manually if no socket event
        const chunkProgress = Math.round(((chunkIndex + 1) / totalChunks) * 100)
        currentFileProgress.value = chunkProgress
        updateTotalProgress()
      }
      
      // Step 3: Finalize upload
      await dataService.finalizeUpload(playlistId, sessionId)
      
      uploadFile.status = 'success'
      uploadFile.progress = 100
      
      console.log(`[RobustUpload] Upload completed: ${file.name}`)
      
    } catch (error) {
      console.error(`[RobustUpload] Upload failed for ${file.name}:`, error)
      uploadFile.status = 'error'
      uploadFile.error = error instanceof Error ? error.message : 'Upload failed'
      
      errors.value.push({
        filename: file.name,
        message: uploadFile.error
      })
      
      throw error
    }
  }

  /**
   * Start upload process for all files
   */
  async function startUpload(playlistId: string) {
    if (uploadFiles.value.length === 0) {
      console.warn('[RobustUpload] No files to upload')
      return
    }
    
    isUploading.value = true
    isCancelled.value = false
    startTime.value = Date.now()
    lastProgressTime.value = startTime.value
    
    setupSocketListeners()
    
    console.log(`[RobustUpload] Starting upload of ${uploadFiles.value.length} files`)
    
    try {
      // Process files one by one to avoid concurrency issues
      for (let i = 0; i < uploadFiles.value.length; i++) {
        if (isCancelled.value) {
          console.log('[RobustUpload] Upload cancelled')
          break
        }
        
        currentFileIndex.value = i
        currentFile.value = uploadFiles.value[i].file
        currentFileProgress.value = 0
        uploadFiles.value[i].status = 'uploading'
        
        try {
          await uploadSingleFile(playlistId, uploadFiles.value[i])
          
          // Small delay between files to ensure backend stability
          if (i < uploadFiles.value.length - 1) {
            await new Promise(resolve => setTimeout(resolve, 200))
          }
          
        } catch (error) {
          console.error(`[RobustUpload] File ${i + 1} failed:`, error)
          // Continue with next file even if this one failed
        }
      }
      
    } finally {
      isUploading.value = false
      currentFileIndex.value = -1
      currentFile.value = null
      cleanupSocketListeners()
      
      const successCount = uploadFiles.value.filter(f => f.status === 'success').length
      const errorCount = uploadFiles.value.filter(f => f.status === 'error').length
      
      console.log(`[RobustUpload] Upload completed: ${successCount} success, ${errorCount} errors`)
    }
  }

  /**
   * Cancel ongoing upload
   */
  async function cancelUpload() {
    console.log('[RobustUpload] Cancelling upload...')
    isCancelled.value = true
    
    // TODO: Call backend cleanup API for uploaded sessions
    for (const sessionId of uploadedSessions.value) {
      try {
        // await dataService.cancelUploadSession(sessionId)
        console.log(`[RobustUpload] Should cancel session: ${sessionId}`)
      } catch (error) {
        console.warn(`[RobustUpload] Failed to cancel session ${sessionId}:`, error)
      }
    }
    
    // Reset state
    uploadFiles.value.forEach(file => {
      if (file.status === 'uploading') {
        file.status = 'error'
        file.error = 'Cancelled by user'
      }
    })
    
    cleanupSocketListeners()
  }

  /**
   * Reset upload state
   */
  function resetUpload() {
    uploadFiles.value = []
    errors.value = []
    uploadedSessions.value = []
    currentFileIndex.value = -1
    currentFile.value = null
    currentFileProgress.value = 0
    totalProgress.value = 0
    isUploading.value = false
    isCancelled.value = false
    uploadSpeed.value = 0
    estimatedTimeRemaining.value = 0
    
    cleanupSocketListeners()
  }

  return {
    // State
    isUploading: readonly(isUploading),
    uploadFiles: readonly(uploadFiles),
    currentFileIndex: readonly(currentFileIndex),
    currentFile: readonly(currentFile),
    currentFileProgress: readonly(currentFileProgress),
    totalProgress: readonly(totalProgress),
    errors: readonly(errors),
    isCancelled: readonly(isCancelled),
    
    // Progress info
    uploadSpeed: readonly(uploadSpeed),
    estimatedTimeRemaining: readonly(estimatedTimeRemaining),
    
    // Actions
    initializeFiles,
    startUpload,
    cancelUpload,
    resetUpload
  }
}

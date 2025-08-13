import { ref, computed } from 'vue'
import dataService from '@/services/dataService'
import socketService from '@/services/socketService'

interface UploadFile {
  file: File
  name: string
  size: number
  status: 'pending' | 'uploading' | 'success' | 'error'
  progress: number
  error?: string
  sessionId?: string
}

interface UploadError {
  filename: string
  message: string
}

export function useModalUpload() {
  // State
  const files = ref<File[]>([])
  const uploadFiles = ref<UploadFile[]>([])
  const currentFileIndex = ref(0)
  const currentFile = ref<File | null>(null)
  const currentFileProgress = ref(0)
  const overallProgress = ref(0)
  const uploadSpeed = ref(0)
  const estimatedTime = ref(0)
  const errors = ref<UploadError[]>([])
  const isUploading = ref(false)
  const isComplete = ref(false)
  const isCancelled = ref(false)
  
  // Stats
  const startTime = ref(0)
  const bytesUploaded = ref(0)
  const lastProgressTime = ref(0)
  const lastBytesUploaded = ref(0)
  
  // Session tracking for cancellation
  const uploadedSessions = ref<string[]>([])
  
  // Computed
  const successCount = computed(() => 
    uploadFiles.value.filter(f => f.status === 'success').length
  )
  
  const errorCount = computed(() => 
    uploadFiles.value.filter(f => f.status === 'error').length
  )
  
  // Socket.IO event handlers
  function setupSocketListeners() {
    socketService.on('upload_progress', handleUploadProgress)
    socketService.on('upload_complete', handleUploadComplete)
    socketService.on('upload_error', handleUploadError)
  }
  
  function cleanupSocketListeners() {
    socketService.off('upload_progress')
    socketService.off('upload_complete')
    socketService.off('upload_error')
  }
  
  function handleUploadProgress(data: any) {
    if (!isUploading.value) return
    
    // Update current file progress
    currentFileProgress.value = data.percentage || 0
    
    // Calculate upload speed
    const now = Date.now()
    const timeDiff = (now - lastProgressTime.value) / 1000
    if (timeDiff > 0.5) { // Update speed every 500ms
      const bytesDiff = data.bytes_uploaded - lastBytesUploaded.value
      uploadSpeed.value = bytesDiff / timeDiff
      lastProgressTime.value = now
      lastBytesUploaded.value = data.bytes_uploaded
      
      // Estimate remaining time
      const remainingBytes = data.total_size - data.bytes_uploaded
      if (uploadSpeed.value > 0) {
        estimatedTime.value = remainingBytes / uploadSpeed.value
      }
    }
    
    updateOverallProgress()
  }
  
  function handleUploadComplete(data: any) {
    console.log('[ModalUpload] File upload complete:', data.filename)
    if (currentFileIndex.value < uploadFiles.value.length) {
      uploadFiles.value[currentFileIndex.value].status = 'success'
      uploadFiles.value[currentFileIndex.value].progress = 100
    }
  }
  
  function handleUploadError(data: any) {
    console.error('[ModalUpload] Upload error:', data)
    errors.value.push({
      filename: data.filename || 'Unknown',
      message: data.error || 'Upload failed'
    })
    
    if (currentFileIndex.value < uploadFiles.value.length) {
      uploadFiles.value[currentFileIndex.value].status = 'error'
      uploadFiles.value[currentFileIndex.value].error = data.error
    }
  }
  
  function updateOverallProgress() {
    const totalFiles = uploadFiles.value.length
    if (totalFiles === 0) {
      overallProgress.value = 0
      return
    }
    
    const completedFiles = currentFileIndex.value
    const currentProgress = currentFileProgress.value / 100
    overallProgress.value = ((completedFiles + currentProgress) / totalFiles) * 100
  }
  
  // Main upload function
  async function startUpload(playlistId: string) {
    if (files.value.length === 0) return
    
    isUploading.value = true
    isComplete.value = false
    isCancelled.value = false
    errors.value = []
    uploadedSessions.value = []
    
    // Initialize upload files
    uploadFiles.value = files.value.map(file => ({
      file,
      name: file.name,
      size: file.size,
      status: 'pending' as const,
      progress: 0
    }))
    
    // Setup socket listeners
    setupSocketListeners()
    
    // Start timing
    startTime.value = Date.now()
    lastProgressTime.value = startTime.value
    
    // Upload files sequentially with delay to avoid backend concurrency issues
    for (let i = 0; i < files.value.length; i++) {
      if (isCancelled.value) break
      
      // Add small delay between uploads to prevent backend concurrency issues
      if (i > 0) {
        await new Promise(resolve => setTimeout(resolve, 500))
      }
      
      currentFileIndex.value = i
      currentFile.value = files.value[i]
      currentFileProgress.value = 0
      uploadFiles.value[i].status = 'uploading'
      
      try {
        await uploadFile(playlistId, files.value[i], i)
        uploadFiles.value[i].status = 'success'
        uploadFiles.value[i].progress = 100
      } catch (error) {
        console.error('[ModalUpload] Upload failed:', error)
        uploadFiles.value[i].status = 'error'
        uploadFiles.value[i].error = error instanceof Error ? error.message : 'Upload failed'
        errors.value.push({
          filename: files.value[i].name,
          message: error instanceof Error ? error.message : 'Upload failed'
        })
      }
    }
    
    // Cleanup
    isUploading.value = false
    isComplete.value = !isCancelled.value
    currentFile.value = null
    cleanupSocketListeners()
  }
  
  // Upload single file using chunked upload
  async function uploadFile(playlistId: string, file: File, index: number): Promise<void> {
    const chunkSize = 1024 * 1024 // 1MB chunks
    const totalChunks = Math.ceil(file.size / chunkSize)
    
    // Initialize upload session with retry logic
    const uploadParams = {
      filename: file.name,
      total_chunks: totalChunks,
      total_size: file.size
    }
    
    console.log('[ModalUpload] Initializing upload with params:', uploadParams)
    console.log('[ModalUpload] Params types:', {
      filename: typeof uploadParams.filename,
      total_chunks: typeof uploadParams.total_chunks,
      total_size: typeof uploadParams.total_size
    })
    console.log('[ModalUpload] Playlist ID:', playlistId)
    
    let initResponse
    let retryCount = 0
    const maxRetries = 3
    
    while (retryCount < maxRetries) {
      try {
        initResponse = await dataService.initUpload(playlistId, uploadParams)
        if (initResponse.session_id) {
          break // Success, exit retry loop
        }
      } catch (error) {
        console.warn(`[ModalUpload] Upload init attempt ${retryCount + 1} failed:`, error)
        retryCount++
        
        if (retryCount < maxRetries) {
          // Wait before retrying (exponential backoff)
          const delay = Math.pow(2, retryCount) * 1000 // 2s, 4s, 8s
          await new Promise(resolve => setTimeout(resolve, delay))
        } else {
          throw error // Max retries reached, throw the error
        }
      }
    }
    
    if (!initResponse || !initResponse.session_id) {
      throw new Error('Failed to initialize upload session after retries')
    }
    
    const sessionId = initResponse.session_id
    uploadedSessions.value.push(sessionId)
    uploadFiles.value[index].sessionId = sessionId
    
    // Upload chunks
    for (let chunkIndex = 0; chunkIndex < totalChunks; chunkIndex++) {
      if (isCancelled.value) {
        throw new Error('Upload cancelled')
      }
      
      const start = chunkIndex * chunkSize
      const end = Math.min(start + chunkSize, file.size)
      const chunk = file.slice(start, end)
      
      const formData = new FormData()
      formData.append('file', chunk)
      formData.append('session_id', sessionId)
      formData.append('chunk_index', chunkIndex.toString())
      
      await dataService.uploadChunk(playlistId, formData)
      
      // Update progress
      currentFileProgress.value = ((chunkIndex + 1) / totalChunks) * 100
      bytesUploaded.value += chunk.size
      updateOverallProgress()
    }
    
    // Finalize upload
    await dataService.finalizeUpload(playlistId, { session_id: sessionId })
  }
  
  // Cancel upload and delete uploaded files
  async function cancelUpload(playlistId: string) {
    isCancelled.value = true
    isUploading.value = false
    
    // Delete all uploaded files from this session
    if (uploadedSessions.value.length > 0) {
      try {
        // Get successfully uploaded file indices
        const uploadedFiles = uploadFiles.value
          .filter(f => f.status === 'success')
          .map(f => f.name)
        
        if (uploadedFiles.length > 0) {
          // Delete uploaded tracks from playlist
          const playlist = await dataService.getPlaylist(playlistId)
          if (playlist && playlist.tracks) {
            // Find track numbers of recently uploaded files
            const tracksToDelete = playlist.tracks
              .filter((track: any) => uploadedFiles.includes(track.filename))
              .map((track: any) => track.track_number)
            
            if (tracksToDelete.length > 0) {
              // Delete tracks one by one since API only supports single track deletion
              for (const trackNumber of tracksToDelete) {
                await dataService.deleteTrack(playlistId, trackNumber)
              }
              console.log('[ModalUpload] Deleted uploaded tracks:', tracksToDelete)
            }
          }
        }
      } catch (error) {
        console.error('[ModalUpload] Failed to delete uploaded files:', error)
      }
    }
    
    cleanupSocketListeners()
  }
  
  // Reset state
  function reset() {
    files.value = []
    uploadFiles.value = []
    currentFileIndex.value = 0
    currentFile.value = null
    currentFileProgress.value = 0
    overallProgress.value = 0
    uploadSpeed.value = 0
    estimatedTime.value = 0
    errors.value = []
    isUploading.value = false
    isComplete.value = false
    isCancelled.value = false
    uploadedSessions.value = []
    bytesUploaded.value = 0
    lastBytesUploaded.value = 0
    cleanupSocketListeners()
  }
  
  return {
    // State
    files,
    currentFile,
    currentFileIndex,
    currentFileProgress,
    overallProgress,
    uploadSpeed,
    estimatedTime,
    errors,
    successCount,
    errorCount,
    isUploading,
    isComplete,
    
    // Actions
    startUpload,
    cancelUpload,
    reset
  }
}

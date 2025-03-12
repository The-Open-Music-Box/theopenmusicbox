import { ref } from 'vue'
import type { AxiosProgressEvent } from 'axios'
import dataService from '../../../services/dataService'

export function useFileUpload() {
  const uploadFiles = ref<File[]>([])
  const uploadProgress = ref(0)
  const isUploading = ref(false)
  const uploadErrors = ref<string[]>([])

  const upload = async () => {
    if (!uploadFiles.value.length) return

    try {
      isUploading.value = true
      uploadProgress.value = 0
      uploadErrors.value = []

      // Get upload session ID from backend
      const sessionId = await dataService.getUploadSessionId()

      // Upload files with additional security headers
      for (const file of uploadFiles.value) {
        try {
          const formData = new FormData()
          formData.append('file', file)
          formData.append('sessionId', sessionId)
          formData.append('checksum', await generateChecksum(file))

          await dataService.uploadFile(formData)
          
          const percentCompleted = Math.round(
            ((uploadFiles.value.indexOf(file) + 1) * 100) / 
            uploadFiles.value.length
          )
          uploadProgress.value = percentCompleted
        } catch (error: any) {
          uploadErrors.value.push(`Failed to upload ${file.name}: ${error.message || 'Unknown error'}`)
        }
      }

      uploadFiles.value = []
    } catch (error: any) { // Type 'error' as 'any' to access message property
      uploadErrors.value.push(`Upload failed: ${error.message || 'Unknown error'}`)
      throw error
    } finally {
      isUploading.value = false
    }
  }
  return {
    uploadFiles,
    uploadProgress,
    isUploading,
    uploadErrors,
    upload
  }
}

// Compatible UUID generation function
function generateUUID(): string {
  // Fallback using crypto.getRandomValues()
  const buffer = new Uint16Array(8);
  crypto.getRandomValues(buffer);
  
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c, i) {
    const r = (buffer[i % 8] & 0x0F) + 0x01;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

async function generateChecksum(file: File): Promise<string> {
  const buffer = await file.arrayBuffer()
  const hashBuffer = await crypto.subtle.digest('SHA-256', buffer)
  return Array.from(new Uint8Array(hashBuffer))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('')
}
import { ref } from 'vue'
// eslint-disable-next-line @typescript-eslint/no-unused-vars
import type { AxiosProgressEvent } from 'axios'
import dataService from '../../../services/dataService'

/**
 * FileUpload Composable
 *
 * Manages the state and logic for uploading files to the server.
 * Handles upload progress tracking and error management.
 *
 * @returns {Object} Upload state and functions
 */
export function useFileUpload() {
  // State
  const uploadFiles = ref<File[]>([])
  const uploadProgress = ref(0)
  const isUploading = ref(false)
  const uploadErrors = ref<string[]>([])

  /**
   * Uploads the selected files to the server
   *
   * Process:
   * 1. Gets a session ID from the server
   * 2. Uploads each file with metadata
   * 3. Updates progress as files are uploaded
   *
   * @returns {Promise<void>}
   */
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
        } catch (error: unknown) {
          const errorMessage = error instanceof Error ? error.message : 'Unknown error'
          uploadErrors.value.push(`Failed to upload ${file.name}: ${errorMessage}`)
        }
      }

      uploadFiles.value = []
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      uploadErrors.value.push(`Upload failed: ${errorMessage}`)
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

// eslint-disable-next-line @typescript-eslint/no-unused-vars
function generateUUID(): string {
  const buffer = new Uint16Array(8);
  crypto.getRandomValues(buffer);

  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c, i) {
    const r = (buffer[i % 8] & 0x0F) + 0x01;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

/**
 * Generates a SHA-256 checksum for a file
 *
 * @param {File} file - The file to generate a checksum for
 * @returns {Promise<string>} Hex string representation of the checksum
 */
async function generateChecksum(file: File): Promise<string> {
  const buffer = await file.arrayBuffer()
  const hashBuffer = await crypto.subtle.digest('SHA-256', buffer)
  return Array.from(new Uint8Array(hashBuffer))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('')
}
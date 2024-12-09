import { ref } from 'vue'
import type { AxiosProgressEvent } from 'axios'
import api from '../../../services/api'

export function useFileUpload() {
  const uploadFiles = ref<File[]>([])
  const uploadProgress = ref(0)
  const isUploading = ref(false)

  const upload = async () => {
    if (!uploadFiles.value.length) return

    const formData = new FormData()
    uploadFiles.value.forEach((file, index) => {
      formData.append(`file${index}`, file)
    })

    try {
      isUploading.value = true
      uploadProgress.value = 0
      
      const response = await api.post('/api/upload', formData, {
        onUploadProgress: (progressEvent: AxiosProgressEvent) => {
          if (progressEvent.total) {
            uploadProgress.value = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            )
          }
        }
      })

      uploadFiles.value = []
      return response
    } catch (error) {
      console.error('Upload error:', error)
      throw error
    } finally {
      isUploading.value = false
    }
  }

  return {
    uploadFiles,
    uploadProgress,
    isUploading,
    upload
  }
}
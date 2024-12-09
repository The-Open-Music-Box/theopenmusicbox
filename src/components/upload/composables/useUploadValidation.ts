import { ref } from 'vue'

export function useUploadValidation() {
  const validationErrors = ref<string[]>([])

  const validateFiles = async (files: File[]) => {
    validationErrors.value = []
    const validFiles: File[] = []

    for (const file of files) {
      // Validate file type
      if (!file.type.startsWith('audio/')) {
        validationErrors.value.push(`${file.name} is not an audio file`)
        continue
      }

      // Validate file size (e.g., 100MB limit)
      if (file.size > 100 * 1024 * 1024) {
        validationErrors.value.push(`${file.name} exceeds the 100MB limit`)
        continue
      }

      validFiles.push(file)
    }

    return validFiles
  }

  return {
    validateFiles,
    validationErrors
  }
}

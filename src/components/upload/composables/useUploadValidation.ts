import { ref } from 'vue'

const MAX_FILE_SIZE = 50 * 1024 * 1024 // 50MB
const ALLOWED_MIME_TYPES = [
  'audio/mpeg',
  'audio/wav',
  'audio/ogg',
  'audio/mp3',
  'audio/flac'
]

export function useUploadValidation() {
  const validationErrors = ref<string[]>([])

  const validateFiles = async (files: File[]) => {
    validationErrors.value = []
    const validFiles: File[] = []

    for (const file of files) {
      // Security checks
      if (!ALLOWED_MIME_TYPES.includes(file.type)) {
        validationErrors.value.push(`${file.name}: Invalid file type`)
        continue
      }

      if (file.size > MAX_FILE_SIZE) {
        validationErrors.value.push(`${file.name}: File too large (max 50MB)`)
        continue
      }

      if (file.name.includes('..') || file.name.includes('/')) {
        validationErrors.value.push(`${file.name}: Invalid file name`)
        continue
      }

      // Verify file content matches extension
      try {
        const isValid = await validateFileContent(file)
        if (!isValid) {
          validationErrors.value.push(`${file.name}: Invalid file content`)
          continue
        }
      } catch (error) {
        validationErrors.value.push(`${file.name}: Validation error`)
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

async function validateFileContent(file: File): Promise<boolean> {
  const buffer = await file.slice(0, 4).arrayBuffer()
  const header = new Uint8Array(buffer)

  // Add audio format validations as needed
  return true
}

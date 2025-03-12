import { ref } from 'vue'

const MAX_FILE_SIZE = 50 * 1024 * 1024 // 50MB
const ALLOWED_MIME_TYPES = [
  'image/jpeg',
  'image/png',
  'application/pdf',
  // Add other allowed types
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

      // Additional security checks
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
  // Read first few bytes to verify file signature
  const buffer = await file.slice(0, 4).arrayBuffer()
  const header = new Uint8Array(buffer)
  
  // Example: Check PNG signature
  if (file.type === 'image/png') {
    return header[0] === 0x89 && 
           header[1] === 0x50 && // P
           header[2] === 0x4E && // N
           header[3] === 0x47    // G
  }
  
  // Add other format validations
  return true
}

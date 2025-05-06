import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

/**
 * UploadValidation Composable
 *
 * Provides functionality to validate files before uploading.
 * Checks file types, sizes, and other validation rules.
 */
export function useUploadValidation() {
  const { t } = useI18n()
  const validationErrors = ref<string[]>([])

  /**
   * Maximum allowed file size in bytes (50MB)
   */
  const MAX_FILE_SIZE = 50 * 1024 * 1024

  /**
   * Allowed audio MIME types
   */
  const ALLOWED_TYPES = [
    'audio/mpeg',
    'audio/mp3',
    'audio/wav',
    'audio/wave',
    'audio/x-wav',
    'audio/ogg',
    'audio/flac',
    'audio/x-flac'
  ]

  /**
   * Validates file size
   * @param {File} file - File to validate
   * @returns {boolean} Whether file size is valid
   */
  const validateFileSize = (file: File): boolean => {
    if (file.size > MAX_FILE_SIZE) {
      validationErrors.value.push(
        `${file.name}: ${t('upload.fileTooLarge', { size: Math.round(MAX_FILE_SIZE / 1024 / 1024) })}`
      )
      return false
    }
    return true
  }

  /**
   * Validates file type
   * @param {File} file - File to validate
   * @returns {boolean} Whether file type is valid
   */
  const validateFileType = (file: File): boolean => {
    if (!ALLOWED_TYPES.includes(file.type)) {
      validationErrors.value.push(
        `${file.name}: ${t('upload.invalidFileType')}`
      )
      return false
    }
    return true
  }

  /**
   * Validate an array of files
   * @param {File[]} files - Array of files to validate
   * @returns {File[]} Array of valid files
   */
  const validateFiles = async (files: File[]): Promise<File[]> => {
    validationErrors.value = []

    const validFiles = files.filter(file => {
      const isSizeValid = validateFileSize(file)
      const isTypeValid = validateFileType(file)
      return isSizeValid && isTypeValid
    })

    return validFiles
  }

  return {
    validateFiles,
    validationErrors
  }
}

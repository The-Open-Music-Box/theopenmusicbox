/**
 * Modal Upload Composable
 * 
 * A specialized composable for managing upload modals with integrated state management.
 * Provides modal-specific functionality while leveraging the unified upload system.
 * 
 * Features:
 * - Modal state management integration
 * - Upload progress tracking for modal UI
 * - Modal-specific error handling
 * - Automatic modal lifecycle management
 * - Integration with upload store
 */

import { ref, computed, watch } from 'vue'
import { useUploadStore } from '@/stores/uploadStore'
import { useUnifiedUpload, type UploadConfig } from './useUnifiedUpload'
import type { UploadError } from '@/types/errors'
import { logger } from '@/utils/logger'

// Modal-specific configuration
export interface ModalUploadConfig extends UploadConfig {
  autoCloseOnSuccess: boolean
  autoCloseDelay: number
  showProgressInTitle: boolean
  persistModalState: boolean
}

/**
 * Modal Upload Composable
 * 
 * Provides upload functionality specifically designed for modal interfaces
 * with integrated state management and modal lifecycle handling.
 */
export function useModalUpload(config: Partial<ModalUploadConfig> = {}) {
  // Modal-specific configuration
  const modalConfig: ModalUploadConfig = {
    chunkSize: 1024 * 1024, // 1MB
    maxRetries: 3,
    useChunkedUpload: true,
    validateFiles: true,
    generateChecksums: false, // Disabled for modal performance
    autoCloseOnSuccess: false, // Let parent component decide
    autoCloseDelay: 2000,
    showProgressInTitle: true,
    persistModalState: true,
    ...config
  }

  // Get upload store for modal state management
  const uploadStore = useUploadStore()

  // Modal-specific state
  const modalTitle = ref<string>('')
  const modalSubtitle = ref<string>('')
  const showSuccessMessage = ref<boolean>(false)
  const successMessage = ref<string>('')
  const autoCloseTimer = ref<number | null>(null)

  // Enhanced error handling for modal context
  const handleModalError = (error: UploadError) => {
    logger.error('Modal upload error', { error }, 'ModalUpload')
    
    // Update modal state to show error
    modalTitle.value = 'Upload Error'
    modalSubtitle.value = error.message || 'An error occurred during upload'
    
    // Clear any success state
    showSuccessMessage.value = false
    clearAutoCloseTimer()
  }

  // Get base upload functionality
  const baseUpload = useUnifiedUpload(modalConfig, handleModalError)

  // Auto-close timer management
  const clearAutoCloseTimer = () => {
    if (autoCloseTimer.value) {
      clearTimeout(autoCloseTimer.value)
      autoCloseTimer.value = null
    }
  }

  const scheduleAutoClose = () => {
    if (modalConfig.autoCloseOnSuccess) {
      clearAutoCloseTimer()
      autoCloseTimer.value = window.setTimeout(() => {
        uploadStore.closeUploadModal()
      }, modalConfig.autoCloseDelay)
    }
  }

  // Computed properties for modal UI
  const modalProgressTitle = computed(() => {
    if (!modalConfig.showProgressInTitle || !baseUpload.isUploading.value) {
      return modalTitle.value
    }
    
    const progress = baseUpload.overallProgress.value
    return `${modalTitle.value} (${progress}%)`
  })

  const isModalBusy = computed(() => 
    baseUpload.isUploading.value || showSuccessMessage.value
  )

  const canCloseModal = computed(() => 
    !baseUpload.isUploading.value && !autoCloseTimer.value
  )

  const modalActions = computed(() => {
    const actions = []
    
    if (baseUpload.isUploading.value) {
      actions.push({
        label: 'Cancel',
        action: 'cancel',
        variant: 'secondary',
        disabled: false
      })
    } else if (baseUpload.uploadFiles.value.length > 0 && !showSuccessMessage.value) {
      actions.push({
        label: 'Upload',
        action: 'upload',
        variant: 'primary',
        disabled: baseUpload.uploadFiles.value.length === 0
      })
      actions.push({
        label: 'Cancel',
        action: 'close',
        variant: 'secondary',
        disabled: false
      })
    } else {
      actions.push({
        label: 'Close',
        action: 'close',
        variant: 'primary',
        disabled: false
      })
    }
    
    return actions
  })

  // Watch for upload completion to show success message
  watch([baseUpload.completedFiles, baseUpload.isUploading], ([completed, uploading]) => {
    if (!uploading && completed > 0 && baseUpload.failedFiles.value === 0) {
      showSuccessMessage.value = true
      successMessage.value = `Successfully uploaded ${completed} file${completed > 1 ? 's' : ''}`
      modalTitle.value = 'Upload Complete'
      modalSubtitle.value = successMessage.value
      
      scheduleAutoClose()
    }
  })

  // Watch for modal open/close to reset state
  watch(() => uploadStore.isModalOpen, (isOpen) => {
    if (isOpen) {
      // Reset state when modal opens
      modalTitle.value = 'Upload Files'
      modalSubtitle.value = 'Select files to upload to your playlist'
      showSuccessMessage.value = false
      successMessage.value = ''
      clearAutoCloseTimer()
    } else {
      // Cleanup when modal closes
      if (baseUpload.isUploading.value) {
        baseUpload.cancelUpload()
      }
      clearAutoCloseTimer()
    }
  })

  // Enhanced upload method with modal integration
  const startModalUpload = async (playlistId?: string): Promise<void> => {
    const targetPlaylistId = playlistId || uploadStore.modalPlaylistId || ''
    
    if (!targetPlaylistId) {
      throw new Error('No playlist ID provided for upload')
    }

    try {
      modalTitle.value = 'Uploading Files'
      modalSubtitle.value = 'Please wait while your files are uploaded...'
      showSuccessMessage.value = false
      
      await baseUpload.startUpload(targetPlaylistId)
      
    } catch (error) {
      logger.error('Modal upload failed', { error, playlistId: targetPlaylistId }, 'ModalUpload')
      throw error
    }
  }

  // Modal action handlers
  const handleModalAction = async (action: string) => {
    switch (action) {
      case 'upload':
        await startModalUpload()
        break
      case 'cancel':
        baseUpload.cancelUpload()
        break
      case 'close':
        uploadStore.closeUploadModal()
        break
      case 'retry':
        await startModalUpload()
        break
      default:
        logger.warn('Unknown modal action', { action }, 'ModalUpload')
    }
  }

  // Enhanced reset with modal state cleanup
  const resetModalUpload = () => {
    baseUpload.resetUpload()
    modalTitle.value = 'Upload Files'
    modalSubtitle.value = 'Select files to upload to your playlist'
    showSuccessMessage.value = false
    successMessage.value = ''
    clearAutoCloseTimer()
  }

  // Modal-specific file initialization
  const initializeModalFiles = (files: File[]) => {
    baseUpload.initializeFiles(files)
    
    if (files.length > 0) {
      modalTitle.value = `Upload ${files.length} File${files.length > 1 ? 's' : ''}`
      modalSubtitle.value = `Ready to upload ${files.length} file${files.length > 1 ? 's' : ''} to your playlist`
    }
  }

  return {
    // Base upload functionality
    ...baseUpload,
    
    // Modal-specific configuration
    modalConfig,
    
    // Modal state
    modalTitle,
    modalSubtitle: computed(() => modalSubtitle.value),
    modalProgressTitle,
    showSuccessMessage,
    successMessage,
    isModalBusy,
    canCloseModal,
    modalActions,
    
    // Upload store integration
    isModalOpen: computed(() => uploadStore.isModalOpen),
    modalPlaylistId: computed(() => uploadStore.modalPlaylistId),
    
    // Enhanced methods
    startUpload: startModalUpload,
    initializeFiles: initializeModalFiles,
    resetUpload: resetModalUpload,
    handleModalAction,
    
    // Modal control methods
    openModal: (playlistId?: string) => {
      if (playlistId) {
        uploadStore.openUploadModal(playlistId)
      }
    },
    closeModal: () => uploadStore.closeUploadModal(),
    
    // Utility methods
    clearAutoCloseTimer
  }
}

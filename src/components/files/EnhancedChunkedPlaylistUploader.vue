<template>
  <UploadErrorBoundary>
    <div class="enhanced-chunked-playlist-uploader">
      <!-- Upload zone -->
      <div
        @dragover.prevent="dragOver"
        @dragleave.prevent="dragLeave"
        @drop.prevent="handleDrop"
        :class="[
          'border-2 border-dashed rounded-md p-4 text-center transition-colors',
          isDragging ? 'border-success bg-success bg-opacity-5' : 'border-border',
          isUploading ? 'opacity-50' : 'hover:border-primary'
        ]"
      >
        <div class="flex flex-col items-center justify-center space-y-2">
          <!-- Upload icon -->
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-6 w-6 text-disabled"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
            />
          </svg>

          <!-- Upload text -->
          <div class="text-sm text-onBackground">
            <p>{{ t('file.dragDropOrClick') }}</p>
            <p class="text-xs text-disabled">{{ t('file.supportedFormats') }}</p>
          </div>

          <!-- Hidden file input -->
          <input
            ref="fileInput"
            type="file"
            multiple
            accept="audio/*"
            class="hidden"
            @change="handleFileSelect"
            :disabled="isUploading"
          />

          <!-- Browse button -->
          <button
            type="button"
            @click.prevent="triggerFileInput"
            :disabled="isUploading"
            class="px-3 py-1.5 bg-primary text-onPrimary rounded-md text-sm hover:bg-primary-light disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ t('file.browseFiles') }}
          </button>
        </div>
      </div>

      <!-- Upload Progress -->
      <div v-if="isUploading || uploadProgress > 0" class="mt-4">
        <div class="flex justify-between items-center mb-2">
          <span class="text-sm font-medium text-onBackground">
            {{ t('file.uploading') }} {{ currentFileName || '' }}
          </span>
          <span class="text-sm text-disabled">
            {{ formatProgress(uploadProgress) }}%
          </span>
        </div>
        
        <!-- Progress bar -->
        <div class="w-full bg-border rounded-full h-2 mb-2">
          <div 
            class="bg-success h-2 rounded-full transition-all duration-300"
            :style="{ width: `${uploadProgress}%` }"
          ></div>
        </div>
        
        <!-- Upload stats -->
        <div v-if="estimatedTimeRemaining" class="text-xs text-disabled">
          {{ t('file.estimatedTimeRemaining') }}: {{ formatTime(estimatedTimeRemaining) }}
        </div>
        
        <!-- Cancel button -->
        <button
          v-if="isUploading"
          @click.prevent="handleCancelUpload"
          class="mt-2 px-3 py-1 bg-error text-onError rounded text-xs hover:bg-error-light"
        >
          {{ t('common.cancel') }}
        </button>
      </div>

      <!-- Upload Errors -->
      <div v-if="uploadErrors.length > 0" class="mt-4">
        <div class="bg-error bg-opacity-10 border border-error rounded-md p-3">
          <h4 class="text-sm font-medium text-error mb-2">{{ t('file.uploadErrors') }}</h4>
          <ul class="text-xs text-error space-y-1">
            <li v-for="(error, index) in uploadErrors" :key="index">{{ error }}</li>
          </ul>
          <button
            @click.prevent="clearErrors"
            class="mt-2 text-xs text-error hover:text-error-light underline"
          >
            {{ t('common.clear') }}
          </button>
        </div>
      </div>

      <!-- Upload State Debug Info -->
      <div v-if="uploadState !== 'idle'" class="mt-2 text-xs text-disabled">
        State: {{ uploadState }}
      </div>
    </div>
  </UploadErrorBoundary>
</template>

<script setup lang="ts">
import { ref, onBeforeUnmount } from 'vue'
import { useEnhancedChunkedUpload } from '../upload/composables/useEnhancedChunkedUpload'
import { useI18n } from 'vue-i18n'
import UploadErrorBoundary from '../upload/UploadErrorBoundary.vue'

const { t } = useI18n()

const props = defineProps<{
  playlistId: string
}>()

const emit = defineEmits<{
  'upload-complete': []
  'upload-error': [error: any]
  'all-uploads-complete': [playlistId: string]
}>()

// References
const fileInput = ref<HTMLInputElement>()

// Enhanced upload composable
const {
  uploadFiles,
  uploadProgress,
  isUploading,
  uploadErrors,
  uploadState,
  currentFileName,
  estimatedTimeRemaining,
  currentProgressPercent,
  upload,
  cancelUpload,
  handleError,
  safeAsync
} = useEnhancedChunkedUpload()

// UI state
const isDragging = ref(false)

/**
 * Trigger file input click
 */
function triggerFileInput() {
  fileInput.value?.click()
}

/**
 * Handle drag over event
 */
function dragOver(event: DragEvent) {
  event.preventDefault()
  event.stopPropagation()
  isDragging.value = true
}

/**
 * Handle drag leave event
 */
function dragLeave(event: DragEvent) {
  event.preventDefault()
  event.stopPropagation()
  isDragging.value = false
}

/**
 * Handle drop event
 */
function handleDrop(event: DragEvent) {
  event.preventDefault()
  event.stopPropagation()
  isDragging.value = false
  
  const files = Array.from(event.dataTransfer?.files || [])
  if (files.length > 0) {
    // Use setTimeout to prevent any potential sync issues
    setTimeout(() => {
      processFiles(files)
    }, 10)
  }
}

/**
 * Handle file selection from input
 */
function handleFileSelect(event: Event) {
  event.preventDefault()
  event.stopPropagation()
  
  const input = event.target as HTMLInputElement
  if (!input.files || input.files.length === 0) {
    return
  }
  
  const files = Array.from(input.files)
  
  // Use setTimeout to prevent any potential sync issues
  setTimeout(() => {
    processFiles(files)
    // Reset input to allow selecting the same file again
    input.value = ''
  }, 10)
}

/**
 * Process and upload files with enhanced error handling
 */
async function processFiles(files: File[]) {
  // Validate files (only audio files)
  const validFiles = files.filter(file => file.type.startsWith('audio/'))
  
  if (validFiles.length === 0) {
    handleError(new Error(t('file.noValidFiles')), 'File validation')
    return
  }
  
  try {
    // Set the files to upload
    uploadFiles.value = validFiles
    
    // Use the enhanced upload with error boundary
    await safeAsync(async () => {
      await upload(props.playlistId)
      
      // Emit completion event
      emit('upload-complete')
      
      // Optional: Emit a separate event for when ALL uploads are truly complete
      // This allows the parent to decide when to refresh
      if (uploadFiles.value.length === 0) {
        emit('all-uploads-complete', props.playlistId)
      }
      
    }, 'Enhanced upload process', undefined)
    
  } catch (err) {
    emit('upload-error', err)
  }
}

/**
 * Handle upload cancellation
 */
function handleCancelUpload() {
  cancelUpload()
}

/**
 * Clear upload errors
 */
function clearErrors() {
  uploadErrors.value = []
}

/**
 * Format progress with one decimal place
 */
function formatProgress(value: number): string {
  return value.toFixed(1)
}

/**
 * Format time in seconds to a human-readable format
 */
function formatTime(seconds: number): string {
  if (seconds < 60) {
    return `${Math.round(seconds)}s`
  } else {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = Math.round(seconds % 60)
    return `${minutes}m ${remainingSeconds}s`
  }
}

// Clean up on component unmount
onBeforeUnmount(() => {
  if (isUploading.value) {
    cancelUpload()
  }
})
</script>

<style scoped>
/* Component-specific styles can be added here if needed */
</style>

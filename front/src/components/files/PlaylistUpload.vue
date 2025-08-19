<template>
  <div class="playlist-upload">
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
          class="h-8 w-8 text-disabled"
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
          @click="triggerFileInput"
          :disabled="isUploading"
          :class="[
            'mt-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-focus',
            isUploading ? 'bg-primary-light text-onPrimary cursor-not-allowed' : 'bg-primary text-onPrimary hover:bg-primary-light'
          ]"
        >
          {{ t('file.browse') }}
        </button>
      </div>
    </div>

    <!-- Upload progress -->
    <div v-if="isUploading" class="mt-4 space-y-3">
      <div class="bg-background rounded-md p-3 shadow-sm">
        <div class="flex justify-between items-center mb-1">
          <span class="text-sm font-medium text-onBackground">{{ t('file.uploading') }}...</span>
          <button
            @click="cancelUpload"
            class="text-xs text-error hover:text-error-light transition-colors"
          >
            {{ t('common.cancel') }}
          </button>
        </div>
        
        <div class="relative h-2 bg-border rounded-full overflow-hidden">
          <div
            class="absolute top-0 left-0 h-full bg-success transition-all duration-300"
            :style="{ width: `${overallProgress}%` }"
          ></div>
        </div>
        
        <div class="flex justify-between items-center mt-1">
          <span class="text-xs text-disabled">{{ overallProgress.toFixed(1) }}%</span>
        </div>
      </div>
    </div>

    <!-- Error messages -->
    <div v-if="errorMessage || uploadErrors.length > 0" class="mt-3 space-y-2">
      <div v-if="errorMessage" class="text-sm text-error">
        {{ errorMessage }}
      </div>
      <div v-if="uploadErrors.length > 0" class="text-sm text-error">
        <ul class="list-disc list-inside space-y-1">
          <li v-for="(error, index) in uploadErrors" :key="index">{{ error }}</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useUnifiedUpload } from '../upload/composables/useUnifiedUpload'

const { t } = useI18n()

const props = defineProps<{
  playlistId: string
}>()

const emit = defineEmits(['upload-complete', 'upload-error'])

// File input reference
const fileInput = ref<HTMLInputElement | null>(null)

// Upload state
const isDragging = ref(false)
const errorMessage = ref('')

// Get upload utilities
const {
  uploadFiles,
  isUploading,
  overallProgress,
  uploadErrors,
  startUpload,
  cancelUpload,
  initializeFiles,
  validateFile
} = useUnifiedUpload()

/**
 * Trigger file input click
 */
function triggerFileInput() {
  fileInput.value?.click()
}

/**
 * Handle drag over event
 */
function dragOver() {
  isDragging.value = true
}

/**
 * Handle drag leave event
 */
function dragLeave() {
  isDragging.value = false
}

/**
 * Handle file drop event
 * @param {DragEvent} event - Drop event
 */
async function handleDrop(event: DragEvent) {
  isDragging.value = false
  errorMessage.value = ''
  
  if (!event.dataTransfer) return
  
  const files = Array.from(event.dataTransfer.files)
  handleFiles(files)
}

/**
 * Handle file selection from input
 * @param {Event} event - Change event
 */
async function handleFileSelect(event: Event) {
  errorMessage.value = ''
  
  const input = event.target as HTMLInputElement
  if (!input.files || input.files.length === 0) return
  
  const files = Array.from(input.files)
  handleFiles(files)
  
  // Reset input to allow selecting the same file again
  input.value = ''
}

/**
 * Handle file selection from input or drop
 * @param files - Selected files
 */
function handleFiles(files: File[]) {
  if (!files || files.length === 0) return
  
  // Filter valid files using unified validation
  const validFiles = Array.from(files).filter(file => {
    const error = validateFile(file)
    return !error // Keep files that have no validation errors
  })
  
  if (validFiles.length > 0) {
    initializeFiles(validFiles)
  }
}

/**
 * Process and upload files
 */
async function processFiles() {
  try {
    // Start the upload process
    await startUpload(props.playlistId)
    
    // Emit completion event
    emit('upload-complete')
  } catch (err) {
    console.error('[PlaylistUpload] Error uploading files:', err)
    errorMessage.value = t('file.uploadError')
    emit('upload-error', err)
  }
}

/**
 * Format file size in human-readable format
 * @param {number} bytes - Size in bytes
 * @returns {string} Formatted size
 */
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`
}
</script>

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
    <div v-if="uploadingFiles.length > 0" class="mt-4 space-y-3">
      <div v-for="file in uploadingFiles" :key="file.name" class="bg-background rounded-md p-3 shadow-sm">
        <div class="flex justify-between items-center mb-1">
          <span class="text-sm font-medium text-onBackground truncate" :title="file.name">{{ file.name }}</span>
          <span class="text-xs text-disabled">{{ formatFileSize(file.size) }}</span>
        </div>
        
        <div class="relative h-2 bg-border rounded-full overflow-hidden">
          <div
            class="absolute top-0 left-0 h-full bg-success transition-all duration-300"
            :style="{ width: `${file.progress}%` }"
          ></div>
        </div>
        
        <div class="flex justify-between items-center mt-1">
          <span class="text-xs text-disabled">{{ file.progress }}%</span>
          <button
            v-if="file.progress < 100"
            @click="cancelUpload(file)"
            class="text-xs text-error hover:text-error-light transition-colors"
          >
            {{ t('common.cancel') }}
          </button>
          <span v-else class="text-xs text-success">{{ t('file.uploadComplete') }}</span>
        </div>
      </div>
    </div>

    <!-- Error message -->
    <div v-if="errorMessage" class="mt-3 text-sm text-error">
      {{ errorMessage }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useFileUpload } from './composables/useFileUpload'
import { useUploadValidation } from './composables/useUploadValidation'

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
const { uploadFiles, isUploading, uploadingFiles, cancelUpload } = useFileUpload()
const { validateFiles } = useUploadValidation()

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
  await processFiles(files)
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
  await processFiles(files)
  
  // Reset input to allow selecting the same file again
  input.value = ''
}

/**
 * Process and upload files
 * @param {File[]} files - Files to process
 */
async function processFiles(files: File[]) {
  // Validate files
  const { validFiles, errors } = validateFiles(files)
  
  if (errors.length > 0) {
    errorMessage.value = errors.join('. ')
    return
  }
  
  if (validFiles.length === 0) {
    errorMessage.value = t('file.noValidFiles')
    return
  }
  
  try {
    // Upload files to the specific playlist
    await uploadFiles(validFiles, props.playlistId)
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

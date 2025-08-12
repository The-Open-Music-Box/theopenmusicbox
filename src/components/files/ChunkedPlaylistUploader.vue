<template>
  <div class="chunked-playlist-uploader">
    
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
      <div class="flex justify-between text-sm text-onBackground">
        <span>{{ currentFileName }}</span>
        <span>{{ currentChunkIndex }}/{{ totalChunks }}</span>
      </div>
      <div class="overflow-hidden rounded-full bg-background">
        <div
          class="h-2 rounded-full bg-primary transition-all"
          :style="{ width: uploadProgress + '%' }"
        ></div>
      </div>
      <div class="flex justify-between text-xs text-disabled">
        <span>{{ formatProgress(uploadProgress) }}%</span>
        <span v-if="estimatedTimeRemaining > 0">
          {{ formatTime(estimatedTimeRemaining) }} {{ t('upload.remaining') }}
        </span>
      </div>
      <button
        @click="cancelUpload"
        class="mt-2 px-3 py-1.5 rounded-md text-sm font-medium bg-error text-onError transition-colors focus:outline-none focus:ring-2 focus:ring-focus"
      >
        {{ t('common.cancel') }}
      </button>
    </div>

    <!-- Error message -->
    <div v-if="uploadErrors.length > 0" class="mt-4 p-3 bg-error bg-opacity-10 border border-error rounded-md">
      <p class="text-sm text-error font-medium">{{ t('file.uploadError') }}</p>
      <ul class="mt-1 text-xs text-error list-disc list-inside">
        <li v-for="(error, index) in uploadErrors" :key="index">{{ error }}</li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * ChunkedPlaylistUploader Component
 * 
 * Provides a drag-and-drop interface for uploading audio files to a playlist
 * using the chunked upload API. Supports progress tracking and error handling.
 */
import { ref, onBeforeUnmount } from 'vue'
import { useChunkedUpload } from '../upload/composables/useChunkedUpload'
import { useI18n } from 'vue-i18n'

const { t } = useI18n();

const props = defineProps<{
  playlistId: string;
}>();

const emit = defineEmits<{
  'upload-complete': []
  'upload-error': [error: any]
}>();

// References
const fileInput = ref<HTMLInputElement>();

// Drag state
const isDragging = ref(false);

// Use the chunked upload composable
const {
  uploadFiles,
  uploadProgress,
  isUploading,
  uploadErrors,
  estimatedTimeRemaining,
  stats,
  currentFileName,
  currentChunkIndex,
  totalChunks,
  upload,
  cancelUpload
} = useChunkedUpload();

/**
 * Trigger the file input click
 */
function triggerFileInput() {
  fileInput.value?.click();
}

/**
 * Handle drag over event
 */
function dragOver() {
  isDragging.value = true;
}

/**
 * Handle drag leave event
 */
function dragLeave() {
  isDragging.value = false;
}

/**
 * Handle file drop event
 * @param {DragEvent} event - Drop event
 */
async function handleDrop(event: DragEvent) {
  isDragging.value = false;
  
  if (!event.dataTransfer) return;
  
  const files = Array.from(event.dataTransfer.files);
  await processFiles(files);
}

/**
 * Handle file selection from input
 * @param {Event} event - Change event
 */
async function handleFileSelect(event: Event) {
  // Prevent default behavior
  event.preventDefault();
  event.stopPropagation();
  
  // File selection handler is triggered
  
  const input = event.target as HTMLInputElement;
  if (!input.files || input.files.length === 0) {
  
    return;
  }
  

  
  const files = Array.from(input.files);
  
  // Enqueue the processFiles call to happen after the current event loop
  setTimeout(() => {
    processFiles(files);
    
    // Reset input to allow selecting the same file again
    input.value = '';
  }, 10);
  
  return false; // Extra prevention of default behavior
}

/**
 * Process and upload files
 * @param {File[]} files - Files to process
 */
async function processFiles(files: File[]) {
  
  // Validate files (only audio files)
  const validFiles = files.filter(file => file.type.startsWith('audio/'));
  
  if (validFiles.length === 0) {
    uploadErrors.value = [t('file.noValidFiles')];
    return;
  }
  
  try {
    
    // Set the files to upload
    uploadFiles.value = validFiles;
    
    // Start the upload process
    await upload(props.playlistId);
    
    // Emit completion event
    emit('upload-complete');
  } catch (err) {
    emit('upload-error', err);
  }
}

/**
 * Format progress with one decimal place
 * @param {number} value - Progress value
 * @returns {string} Formatted progress
 */
function formatProgress(value: number): string {
  return value.toFixed(1);
}

/**
 * Format time in seconds to a human-readable format
 * @param {number} seconds - Time in seconds
 * @returns {string} Formatted time
 */
function formatTime(seconds: number): string {
  if (seconds < 60) {
    return `${Math.round(seconds)}s`;
  } else {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.round(seconds % 60);
    return `${minutes}m ${remainingSeconds}s`;
  }
}

// Clean up on component unmount
onBeforeUnmount(() => {
  if (isUploading.value) {
    cancelUpload();
  }
});
</script>

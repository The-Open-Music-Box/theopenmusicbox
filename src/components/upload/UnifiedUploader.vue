<template>
  <div class="unified-uploader">
    <!-- Upload Zone -->
    <div
      @dragover.prevent="handleDragOver"
      @dragleave.prevent="handleDragLeave"
      @drop.prevent="handleDrop"
      :class="[
        'border-2 border-dashed rounded-lg p-6 text-center transition-all duration-200',
        isDragging ? 'border-primary bg-primary bg-opacity-5 scale-105' : 'border-gray-300',
        isUploading ? 'opacity-50 cursor-not-allowed' : 'hover:border-primary hover:bg-gray-50 cursor-pointer'
      ]"
      @click="triggerFileInput"
    >
      <div class="flex flex-col items-center justify-center space-y-4">
        <!-- Upload Icon -->
        <div class="w-12 h-12 text-gray-400">
          <svg fill="none" stroke="currentColor" viewBox="0 0 48 48">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
            />
          </svg>
        </div>

        <!-- Upload Text -->
        <div class="text-center">
          <p class="text-lg font-medium text-gray-900">
            {{ t('upload.dragDropFiles') }}
          </p>
          <p class="text-sm text-gray-500 mt-1">
            {{ t('upload.orClickToBrowse') }}
          </p>
          <p class="text-xs text-gray-400 mt-2">
            {{ t('upload.supportedFormats') }}: MP3, WAV, FLAC, OGG, M4A
          </p>
        </div>

        <!-- Browse Button -->
        <button
          type="button"
          :disabled="isUploading"
          class="px-4 py-2 bg-primary text-white rounded-md hover:bg-primary-dark disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {{ t('upload.browseFiles') }}
        </button>
      </div>

      <!-- Hidden File Input -->
      <input
        ref="fileInput"
        type="file"
        multiple
        accept="audio/*"
        class="hidden"
        @change="handleFileSelect"
        :disabled="isUploading"
      />
    </div>

    <!-- Upload Configuration -->
    <div v-if="showAdvancedOptions" class="mt-4 p-4 bg-gray-50 rounded-lg">
      <h4 class="text-sm font-medium text-gray-900 mb-3">{{ t('upload.advancedOptions') }}</h4>
      
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- Chunked Upload Toggle -->
        <div class="flex items-center">
          <input
            id="chunked-upload"
            type="checkbox"
            v-model="uploadConfig.useChunkedUpload"
            class="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded"
          />
          <label for="chunked-upload" class="ml-2 text-sm text-gray-700">
            {{ t('upload.useChunkedUpload') }}
          </label>
        </div>

        <!-- File Validation Toggle -->
        <div class="flex items-center">
          <input
            id="validate-files"
            type="checkbox"
            v-model="uploadConfig.validateFiles"
            class="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded"
          />
          <label for="validate-files" class="ml-2 text-sm text-gray-700">
            {{ t('upload.validateFiles') }}
          </label>
        </div>

        <!-- Checksum Generation Toggle -->
        <div class="flex items-center">
          <input
            id="generate-checksums"
            type="checkbox"
            v-model="uploadConfig.generateChecksums"
            class="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded"
          />
          <label for="generate-checksums" class="ml-2 text-sm text-gray-700">
            {{ t('upload.generateChecksums') }}
          </label>
        </div>

        <!-- Max Retries -->
        <div class="flex items-center space-x-2">
          <label for="max-retries" class="text-sm text-gray-700">
            {{ t('upload.maxRetries') }}:
          </label>
          <input
            id="max-retries"
            type="number"
            min="0"
            max="10"
            v-model.number="uploadConfig.maxRetries"
            class="w-16 px-2 py-1 border border-gray-300 rounded text-sm"
          />
        </div>
      </div>
    </div>

    <!-- File Queue -->
    <div v-if="uploadFiles.length > 0" class="mt-6">
      <div class="flex items-center justify-between mb-4">
        <h4 class="text-lg font-medium text-gray-900">
          {{ t('upload.fileQueue') }} ({{ uploadFiles.length }})
        </h4>
        <div class="flex space-x-2">
          <button
            @click="clearQueue"
            :disabled="isUploading"
            class="px-3 py-1 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:opacity-50"
          >
            {{ t('common.clear') }}
          </button>
          <button
            @click="startUpload"
            :disabled="isUploading || uploadFiles.length === 0"
            class="px-4 py-1 text-sm bg-primary text-white rounded hover:bg-primary-dark disabled:opacity-50"
          >
            {{ isUploading ? t('upload.uploading') : t('upload.startUpload') }}
          </button>
        </div>
      </div>

      <!-- File List -->
      <div class="space-y-2 max-h-60 overflow-y-auto">
        <div
          v-for="(uploadFile, index) in uploadFiles"
          :key="index"
          class="flex items-center justify-between p-3 bg-white border border-gray-200 rounded-lg"
        >
          <div class="flex items-center space-x-3 flex-1">
            <!-- File Icon -->
            <div class="w-8 h-8 flex-shrink-0">
              <svg class="w-full h-full text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clip-rule="evenodd" />
              </svg>
            </div>

            <!-- File Info -->
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium text-gray-900 truncate">
                {{ uploadFile.file.name }}
              </p>
              <p class="text-xs text-gray-500">
                {{ formatFileSize(uploadFile.file.size) }}
              </p>
            </div>

            <!-- Status -->
            <div class="flex items-center space-x-2">
              <div
                :class="[
                  'w-2 h-2 rounded-full',
                  getStatusColor(uploadFile.status)
                ]"
              ></div>
              <span class="text-xs text-gray-500 capitalize">
                {{ uploadFile.status }}
              </span>
            </div>

            <!-- Progress -->
            <div v-if="uploadFile.status === 'uploading'" class="w-20">
              <div class="w-full bg-gray-200 rounded-full h-2">
                <div
                  class="bg-primary h-2 rounded-full transition-all duration-300"
                  :style="{ width: uploadFile.progress + '%' }"
                ></div>
              </div>
              <span class="text-xs text-gray-500">{{ uploadFile.progress }}%</span>
            </div>
          </div>

          <!-- Remove Button -->
          <button
            @click="removeFile(index)"
            :disabled="isUploading && uploadFile.status === 'uploading'"
            class="ml-2 p-1 text-gray-400 hover:text-red-500 disabled:opacity-50"
          >
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Upload Progress -->
    <div v-if="isUploading" class="mt-6">
      <div class="bg-white border border-gray-200 rounded-lg p-4">
        <div class="flex items-center justify-between mb-2">
          <h4 class="text-sm font-medium text-gray-900">
            {{ t('upload.uploadProgress') }}
          </h4>
          <button
            @click="cancelUpload"
            class="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200"
          >
            {{ t('common.cancel') }}
          </button>
        </div>

        <!-- Overall Progress -->
        <div class="mb-4">
          <div class="flex justify-between text-sm text-gray-600 mb-1">
            <span>{{ t('upload.overall') }}</span>
            <span>{{ overallProgress }}%</span>
          </div>
          <div class="w-full bg-gray-200 rounded-full h-2">
            <div
              class="bg-primary h-2 rounded-full transition-all duration-300"
              :style="{ width: overallProgress + '%' }"
            ></div>
          </div>
        </div>

        <!-- Current File -->
        <div v-if="currentFileName" class="mb-4">
          <div class="flex justify-between text-sm text-gray-600 mb-1">
            <span class="truncate">{{ currentFileName }}</span>
            <span>{{ currentFileProgress }}%</span>
          </div>
          <div class="w-full bg-gray-200 rounded-full h-1">
            <div
              class="bg-blue-500 h-1 rounded-full transition-all duration-300"
              :style="{ width: currentFileProgress + '%' }"
            ></div>
          </div>
        </div>

        <!-- Upload Statistics -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-600">
          <div>
            <span class="font-medium">{{ t('upload.speed') }}:</span>
            <span class="ml-1">{{ uploadSpeedFormatted }}</span>
          </div>
          <div>
            <span class="font-medium">{{ t('upload.completed') }}:</span>
            <span class="ml-1">{{ completedFiles }}/{{ stats.filesTotal }}</span>
          </div>
          <div v-if="estimatedTimeRemaining">
            <span class="font-medium">{{ t('upload.timeRemaining') }}:</span>
            <span class="ml-1">{{ formatTime(estimatedTimeRemaining) }}</span>
          </div>
          <div v-if="uploadConfig.useChunkedUpload">
            <span class="font-medium">{{ t('upload.chunks') }}:</span>
            <span class="ml-1">{{ currentChunkIndex }}/{{ totalChunks }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Error Messages -->
    <div v-if="hasErrors" class="mt-4">
      <div class="bg-red-50 border border-red-200 rounded-lg p-4">
        <h4 class="text-sm font-medium text-red-800 mb-2">
          {{ t('upload.errors') }}
        </h4>
        <ul class="text-sm text-red-700 space-y-1">
          <li v-for="(error, index) in uploadErrors" :key="index">
            • {{ error }}
          </li>
        </ul>
      </div>
    </div>

    <!-- Advanced Options Toggle -->
    <div class="mt-4 text-center">
      <button
        @click="showAdvancedOptions = !showAdvancedOptions"
        class="text-sm text-gray-500 hover:text-gray-700"
      >
        {{ showAdvancedOptions ? t('upload.hideAdvanced') : t('upload.showAdvanced') }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useUploadStore } from '../../stores/uploadStore'

const { t } = useI18n()
const uploadStore = useUploadStore()

// Props
const props = defineProps<{
  playlistId: string
}>()

// Emits
const emit = defineEmits<{
  'upload-complete': []
  'upload-error': [error: any]
}>()

// Local state
const fileInput = ref<HTMLInputElement>()
const isDragging = ref(false)
const showAdvancedOptions = ref(false)

// Store state
const {
  uploadFiles,
  isUploading,
  uploadErrors,
  hasErrors,
  overallProgress,
  currentFileProgress,
  currentFileName,
  currentChunkIndex,
  totalChunks,
  stats,
  estimatedTimeRemaining,
  uploadSpeedFormatted,
  completedFiles,
  uploadConfig
} = uploadStore

// Methods
const triggerFileInput = () => {
  if (!isUploading.value) {
    fileInput.value?.click()
  }
}

const handleDragOver = () => {
  isDragging.value = true
}

const handleDragLeave = () => {
  isDragging.value = false
}

const handleDrop = (event: DragEvent) => {
  isDragging.value = false
  
  if (!event.dataTransfer || isUploading.value) return
  
  const files = Array.from(event.dataTransfer.files)
  addFiles(files)
}

const handleFileSelect = (event: Event) => {
  const input = event.target as HTMLInputElement
  if (!input.files || input.files.length === 0) return
  
  const files = Array.from(input.files)
  addFiles(files)
  
  // Reset input
  input.value = ''
}

const addFiles = (files: File[]) => {
  uploadStore.addFilesToQueue(props.playlistId, files)
}

const removeFile = (index: number) => {
  uploadStore.removeFileFromQueue(props.playlistId, index)
}

const clearQueue = () => {
  uploadStore.clearQueue(props.playlistId)
}

const startUpload = async () => {
  try {
    await uploadStore.startUpload(props.playlistId)
    emit('upload-complete')
  } catch (error) {
    emit('upload-error', error)
  }
}

const cancelUpload = () => {
  uploadStore.cancelUpload()
}

// Utility functions
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatTime = (seconds: number): string => {
  if (seconds < 60) return `${Math.round(seconds)}s`
  
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.round(seconds % 60)
  
  return `${minutes}m ${remainingSeconds}s`
}

const getStatusColor = (status: string): string => {
  switch (status) {
    case 'pending': return 'bg-gray-400'
    case 'uploading': return 'bg-blue-500'
    case 'success': return 'bg-green-500'
    case 'error': return 'bg-red-500'
    case 'cancelled': return 'bg-yellow-500'
    default: return 'bg-gray-400'
  }
}
</script>

<style scoped>
.unified-uploader {
  @apply w-full;
}
</style>

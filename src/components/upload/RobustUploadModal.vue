<template>
  <div v-if="isOpen" class="upload-modal-overlay" @click="handleOverlayClick">
    <div class="upload-modal-container" @click.stop>
      <!-- Header -->
      <div class="upload-modal-header">
        <h3 class="upload-modal-title">
          {{ $t('upload.title') }}
        </h3>
        <button 
          class="upload-modal-close"
          @click="handleCancel"
          :disabled="isUploading"
        >
          ×
        </button>
      </div>

      <!-- Upload Area -->
      <div 
        class="upload-dropzone"
        :class="{ 
          'upload-dropzone--dragover': isDragOver,
          'upload-dropzone--uploading': isUploading 
        }"
        @drop="handleDrop"
        @dragover.prevent="isDragOver = true"
        @dragleave="isDragOver = false"
        @click="triggerFileInput"
      >
        <input
          ref="fileInput"
          type="file"
          multiple
          accept="audio/*"
          @change="handleFileSelect"
          style="display: none"
        />
        
        <div v-if="!isUploading && uploadFiles.length === 0" class="upload-dropzone-content">
          <div class="upload-icon">📁</div>
          <p class="upload-text">{{ $t('upload.dropFiles') }}</p>
          <p class="upload-subtext">{{ $t('upload.orClickToSelect') }}</p>
        </div>
        
        <div v-else class="upload-progress-container">
          <!-- Overall Progress -->
          <div class="upload-overall-progress">
            <div class="upload-progress-info">
              <span class="upload-progress-text">
                {{ isUploading ? $t('upload.uploading') : $t('upload.ready') }}
              </span>
              <span class="upload-progress-percentage">{{ totalProgress }}%</span>
            </div>
            <div class="upload-progress-bar">
              <div 
                class="upload-progress-fill" 
                :style="{ width: totalProgress + '%' }"
              ></div>
            </div>
          </div>

          <!-- File List -->
          <div class="upload-file-list">
            <div 
              v-for="(uploadFile, index) in uploadFiles" 
              :key="index"
              class="upload-file-item"
              :class="`upload-file-item--${uploadFile.status}`"
            >
              <div class="upload-file-info">
                <span class="upload-file-name">{{ uploadFile.file.name }}</span>
                <span class="upload-file-size">{{ formatFileSize(uploadFile.file.size) }}</span>
              </div>
              
              <div class="upload-file-status">
                <div v-if="uploadFile.status === 'pending'" class="upload-status-pending">
                  ⏳ {{ $t('upload.pending') }}
                </div>
                <div v-else-if="uploadFile.status === 'uploading'" class="upload-status-uploading">
                  <div class="upload-file-progress">
                    <div 
                      class="upload-file-progress-fill" 
                      :style="{ width: uploadFile.progress + '%' }"
                    ></div>
                  </div>
                  <span>{{ uploadFile.progress }}%</span>
                </div>
                <div v-else-if="uploadFile.status === 'success'" class="upload-status-success">
                  ✅ {{ $t('upload.success') }}
                </div>
                <div v-else-if="uploadFile.status === 'error'" class="upload-status-error">
                  ❌ {{ uploadFile.error || $t('upload.error') }}
                </div>
              </div>
            </div>
          </div>

          <!-- Upload Stats -->
          <div v-if="isUploading && uploadSpeed > 0" class="upload-stats">
            <span class="upload-speed">
              {{ $t('upload.speed') }}: {{ formatSpeed(uploadSpeed) }}
            </span>
            <span class="upload-eta" v-if="estimatedTimeRemaining > 0">
              {{ $t('upload.eta') }}: {{ formatTime(estimatedTimeRemaining) }}
            </span>
          </div>
        </div>
      </div>

      <!-- Error Messages -->
      <div v-if="errors.length > 0" class="upload-errors">
        <h4 class="upload-errors-title">{{ $t('upload.errors') }}</h4>
        <div 
          v-for="error in errors" 
          :key="error.filename"
          class="upload-error-item"
        >
          <strong>{{ error.filename }}:</strong> {{ error.message }}
        </div>
      </div>

      <!-- Actions -->
      <div class="upload-modal-actions">
        <button 
          class="upload-btn upload-btn--secondary"
          @click="handleCancel"
          :disabled="isUploading"
        >
          {{ isUploading ? $t('upload.cancel') : $t('common.cancel') }}
        </button>
        
        <button 
          v-if="uploadFiles.length > 0 && !isUploading"
          class="upload-btn upload-btn--primary"
          @click="handleStartUpload"
        >
          {{ $t('upload.start') }}
        </button>
        
        <button 
          v-if="!isUploading && (uploadFiles.some(f => f.status === 'success') || errors.length === 0)"
          class="upload-btn upload-btn--primary"
          @click="handleConfirm"
        >
          {{ $t('common.ok') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRobustUpload } from './composables/useRobustUpload'
import { useUploadModalStore } from '@/stores/uploadModalStore'

// Props
interface Props {
  playlistId?: string
}

const props = withDefaults(defineProps<Props>(), {
  playlistId: ''
})

// Emits
const emit = defineEmits<{
  close: []
  success: []
}>()

// Upload composable
const {
  isUploading,
  uploadFiles,
  currentFileIndex,
  currentFile,
  currentFileProgress,
  totalProgress,
  errors,
  isCancelled,
  uploadSpeed,
  estimatedTimeRemaining,
  initializeFiles,
  startUpload,
  cancelUpload,
  resetUpload
} = useRobustUpload()

// Local state
const fileInput = ref<HTMLInputElement>()
const isDragOver = ref(false)
const uploadModalStore = useUploadModalStore()

// Computed
const isOpen = computed(() => uploadModalStore.isOpen)
const currentPlaylistId = computed(() => props.playlistId || uploadModalStore.currentPlaylistId)

// File handling
function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.files) {
    const files = Array.from(target.files)
    initializeFiles(files)
  }
}

function handleDrop(event: DragEvent) {
  event.preventDefault()
  isDragOver.value = false
  
  if (event.dataTransfer?.files) {
    const files = Array.from(event.dataTransfer.files).filter(file => 
      file.type.startsWith('audio/')
    )
    if (files.length > 0) {
      initializeFiles(files)
    }
  }
}

function triggerFileInput() {
  if (!isUploading.value) {
    fileInput.value?.click()
  }
}

// Actions
async function handleStartUpload() {
  if (!currentPlaylistId.value) {
    console.error('[RobustUploadModal] No playlist ID provided')
    return
  }
  
  try {
    await startUpload(currentPlaylistId.value)
  } catch (error) {
    console.error('[RobustUploadModal] Upload failed:', error)
  }
}

async function handleCancel() {
  if (isUploading.value) {
    await cancelUpload()
  }
  
  resetUpload()
  uploadModalStore.close()
  emit('close')
}

function handleConfirm() {
  const hasSuccessfulUploads = uploadFiles.value.some(f => f.status === 'success')
  
  resetUpload()
  uploadModalStore.close()
  
  if (hasSuccessfulUploads) {
    emit('success')
  }
  
  emit('close')
}

function handleOverlayClick() {
  if (!isUploading.value) {
    handleCancel()
  }
}

// Utility functions
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

function formatSpeed(bytesPerSecond: number): string {
  return formatFileSize(bytesPerSecond) + '/s'
}

function formatTime(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}s`
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.round(seconds % 60)
  return `${minutes}m ${remainingSeconds}s`
}

// Lifecycle
onMounted(() => {
  // Reset state when modal opens
  if (isOpen.value) {
    resetUpload()
  }
})

onUnmounted(() => {
  resetUpload()
})
</script>

<style scoped>
.upload-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.9));
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.3s ease-out;
}

.upload-modal-container {
  background: linear-gradient(145deg, #ffffff, #f8f9fa);
  border-radius: 16px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow: hidden;
  animation: slideIn 0.3s ease-out;
}

.upload-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.upload-modal-title {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
}

.upload-modal-close {
  background: none;
  border: none;
  color: white;
  font-size: 24px;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s;
}

.upload-modal-close:hover:not(:disabled) {
  background-color: rgba(255, 255, 255, 0.2);
}

.upload-modal-close:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.upload-dropzone {
  margin: 24px;
  padding: 40px 20px;
  border: 2px dashed #cbd5e0;
  border-radius: 12px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background: linear-gradient(145deg, #f7fafc, #edf2f7);
}

.upload-dropzone--dragover {
  border-color: #667eea;
  background: linear-gradient(145deg, #ebf4ff, #dbeafe);
  transform: scale(1.02);
}

.upload-dropzone--uploading {
  cursor: default;
}

.upload-dropzone-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.upload-icon {
  font-size: 48px;
  opacity: 0.6;
}

.upload-text {
  font-size: 1.1rem;
  font-weight: 500;
  color: #2d3748;
  margin: 0;
}

.upload-subtext {
  font-size: 0.9rem;
  color: #718096;
  margin: 0;
}

.upload-progress-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.upload-overall-progress {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.upload-progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.upload-progress-text {
  font-weight: 500;
  color: #2d3748;
}

.upload-progress-percentage {
  font-weight: 600;
  color: #667eea;
}

.upload-progress-bar {
  height: 8px;
  background: #e2e8f0;
  border-radius: 4px;
  overflow: hidden;
}

.upload-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.upload-file-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 200px;
  overflow-y: auto;
}

.upload-file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: white;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.upload-file-item--uploading {
  border-color: #667eea;
  background: #f7faff;
}

.upload-file-item--success {
  border-color: #48bb78;
  background: #f0fff4;
}

.upload-file-item--error {
  border-color: #f56565;
  background: #fffafa;
}

.upload-file-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
  min-width: 0;
}

.upload-file-name {
  font-weight: 500;
  color: #2d3748;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.upload-file-size {
  font-size: 0.8rem;
  color: #718096;
}

.upload-file-status {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.upload-file-progress {
  width: 60px;
  height: 4px;
  background: #e2e8f0;
  border-radius: 2px;
  overflow: hidden;
}

.upload-file-progress-fill {
  height: 100%;
  background: #667eea;
  border-radius: 2px;
  transition: width 0.3s ease;
}

.upload-stats {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.9rem;
  color: #718096;
  padding-top: 8px;
  border-top: 1px solid #e2e8f0;
}

.upload-errors {
  margin: 0 24px 16px;
  padding: 16px;
  background: #fffafa;
  border: 1px solid #fed7d7;
  border-radius: 8px;
}

.upload-errors-title {
  margin: 0 0 12px 0;
  font-size: 1rem;
  font-weight: 600;
  color: #c53030;
}

.upload-error-item {
  font-size: 0.9rem;
  color: #742a2a;
  margin-bottom: 4px;
}

.upload-modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 24px;
  background: #f7fafc;
  border-top: 1px solid #e2e8f0;
}

.upload-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.95rem;
}

.upload-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.upload-btn--secondary {
  background: #e2e8f0;
  color: #4a5568;
}

.upload-btn--secondary:hover:not(:disabled) {
  background: #cbd5e0;
}

.upload-btn--primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.upload-btn--primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideIn {
  from { 
    opacity: 0;
    transform: translateY(-20px) scale(0.95);
  }
  to { 
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}
</style>

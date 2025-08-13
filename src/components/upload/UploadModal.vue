<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div v-if="isVisible" class="modal-overlay" @click.self="handleOverlayClick">
        <div class="modal-container">
          <!-- Header -->
          <div class="modal-header">
            <h2>{{ t('upload.title') }}</h2>
            <button 
              v-if="!isUploading" 
              @click="handleClose"
              class="close-button"
              :aria-label="t('common.close')"
            >
              <i class="fas fa-times"></i>
            </button>
          </div>

          <!-- Body -->
          <div class="modal-body">
            <!-- File Selection -->
            <div v-if="!hasFiles" class="upload-dropzone" 
                 @drop="handleDrop"
                 @dragover.prevent
                 @dragenter.prevent>
              <i class="fas fa-cloud-upload-alt upload-icon"></i>
              <p>{{ t('upload.dragDropHint') }}</p>
              <p class="upload-or">{{ t('common.or') }}</p>
              <label class="file-input-label">
                <input
                  ref="fileInput"
                  type="file"
                  multiple
                  accept="audio/*"
                  @change="handleFileSelect"
                  class="file-input-hidden"
                />
                <span class="btn btn-primary">
                  <i class="fas fa-folder-open"></i>
                  {{ t('upload.selectFiles') }}
                </span>
              </label>
            </div>

            <!-- Upload Progress -->
            <div v-else class="upload-progress-container">
              <!-- Current File -->
              <div v-if="currentFile" class="current-file">
                <div class="file-info">
                  <i class="fas fa-music file-icon"></i>
                  <div class="file-details">
                    <div class="file-name">{{ currentFile.name }}</div>
                    <div class="file-meta">
                      {{ formatFileSize(currentFile.size) }} • 
                      {{ currentFileIndex + 1 }}/{{ totalFiles }}
                    </div>
                  </div>
                </div>
                
                <!-- Progress Bar -->
                <div class="progress-wrapper">
                  <div class="progress-bar-container">
                    <div 
                      class="progress-bar"
                      :style="{ width: `${currentFileProgress}%` }"
                    >
                      <span class="progress-text">{{ Math.round(currentFileProgress) }}%</span>
                    </div>
                  </div>
                  <div class="progress-stats">
                    <span>{{ formatSpeed(uploadSpeed) }}</span>
                    <span v-if="estimatedTime">{{ formatTime(estimatedTime) }}</span>
                  </div>
                </div>
              </div>

              <!-- Overall Progress -->
              <div class="overall-progress">
                <h4>{{ t('upload.overallProgress') }}</h4>
                <div class="progress-bar-container small">
                  <div 
                    class="progress-bar"
                    :style="{ width: `${overallProgress}%` }"
                  ></div>
                </div>
                <div class="files-status">
                  {{ successCount }} {{ t('upload.completed') }} • 
                  {{ errorCount }} {{ t('upload.failed') }}
                </div>
              </div>

              <!-- Error List -->
              <div v-if="errors.length > 0" class="error-list">
                <h4>{{ t('upload.errors') }}</h4>
                <div v-for="(error, idx) in errors" :key="idx" class="error-item">
                  <i class="fas fa-exclamation-circle"></i>
                  <span>{{ error.filename }}: {{ error.message }}</span>
                </div>
              </div>

              <!-- Success Message -->
              <div v-if="isComplete && !hasErrors" class="success-message">
                <i class="fas fa-check-circle"></i>
                <p>{{ t('upload.allFilesUploaded') }}</p>
              </div>
            </div>
          </div>

          <!-- Footer -->
          <div class="modal-footer">
            <button 
              v-if="!isComplete"
              @click="handleCancel"
              class="btn btn-secondary"
              :disabled="!isUploading && !hasFiles"
            >
              <i class="fas fa-ban"></i>
              {{ t('common.cancel') }}
            </button>
            
            <button 
              v-if="isComplete"
              @click="handleOk"
              class="btn btn-primary"
            >
              <i class="fas fa-check"></i>
              {{ t('common.ok') }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useUploadModalStore } from '@/stores/uploadModalStore'
import { useModalUpload } from './composables/useModalUpload'

// Props
interface Props {
  playlistId: string
}

const props = defineProps<Props>()

// i18n
const { t } = useI18n()

// Store
const uploadModalStore = useUploadModalStore()

// Upload composable
const {
  files,
  currentFile,
  currentFileIndex,
  currentFileProgress,
  overallProgress,
  uploadSpeed,
  estimatedTime,
  errors,
  successCount,
  errorCount,
  isUploading,
  isComplete,
  startUpload,
  cancelUpload,
  reset
} = useModalUpload()

// Local state
const fileInput = ref<HTMLInputElement>()

// Computed
const isVisible = computed(() => uploadModalStore.isOpen())
const hasFiles = computed(() => files.value.length > 0)
const hasErrors = computed(() => errors.value.length > 0)
const totalFiles = computed(() => files.value.length)

// Methods
function handleOverlayClick() {
  if (!isUploading.value) {
    handleClose()
  }
}

function handleClose() {
  uploadModalStore.close()
  reset()
}

async function handleCancel() {
  if (isUploading.value) {
    await cancelUpload(props.playlistId)
  }
  handleClose()
}

async function handleOk() {
  // Refresh the playlist to show new tracks
  uploadModalStore.close()
  reset()
  // Emit event to refresh playlists
  window.location.reload() // Simple refresh for now
}

function handleDrop(event: DragEvent) {
  event.preventDefault()
  const droppedFiles = event.dataTransfer?.files
  if (droppedFiles) {
    handleFiles(droppedFiles)
  }
}

function handleFileSelect(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files) {
    handleFiles(input.files)
  }
}

function handleFiles(fileList: FileList) {
  const audioFiles = Array.from(fileList).filter(file => 
    file.type.startsWith('audio/') || 
    file.name.match(/\.(mp3|wav|ogg|m4a|flac|aac)$/i)
  )
  
  if (audioFiles.length === 0) {
    alert(t('upload.noAudioFiles'))
    return
  }
  
  files.value = audioFiles
  startUpload(props.playlistId)
}

// Formatting helpers
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

function formatSpeed(bytesPerSecond: number): string {
  if (!bytesPerSecond) return ''
  return formatFileSize(bytesPerSecond) + '/s'
}

function formatTime(seconds: number): string {
  if (!seconds) return ''
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`
}

// Watch for modal open/close
watch(isVisible, (newVal) => {
  if (!newVal) {
    reset()
  }
})
</script>

<style scoped>
/* Modal Overlay */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(0, 0, 0, 0.8), rgba(0, 0, 0, 0.6));
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 20px;
}

/* Modal Container */
.modal-container {
  background: linear-gradient(145deg, #ffffff, #f8f9fa);
  border-radius: 20px;
  box-shadow: 
    0 25px 80px rgba(0, 0, 0, 0.15),
    0 0 0 1px rgba(255, 255, 255, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
  max-width: 650px;
  width: 100%;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

/* Modal Header */
.modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.modal-header h2 {
  margin: 0;
  font-size: 1.5rem;
  color: var(--color-text);
}

.close-button {
  background: none;
  border: none;
  color: var(--color-text-secondary);
  font-size: 1.5rem;
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s;
}

.close-button:hover {
  color: var(--color-danger);
}

/* Modal Body */
.modal-body {
  padding: 24px;
  flex: 1;
  overflow-y: auto;
}

/* Upload Dropzone */
.upload-dropzone {
  border: 2px dashed #e2e8f0;
  border-radius: 16px;
  padding: 48px 24px;
  text-align: center;
  transition: all 0.3s ease;
  cursor: pointer;
  background: linear-gradient(135deg, #f8fafc, #f1f5f9);
  position: relative;
  overflow: hidden;
}

.upload-dropzone:hover {
  border-color: #3b82f6;
  background: linear-gradient(135deg, #eff6ff, #dbeafe);
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(59, 130, 246, 0.15);
}

.upload-icon {
  font-size: 3.5rem;
  color: #3b82f6;
  margin-bottom: 20px;
  filter: drop-shadow(0 4px 8px rgba(59, 130, 246, 0.2));
}

.upload-or {
  margin: 16px 0;
  color: var(--color-text-secondary);
  font-size: 0.9rem;
}

.file-input-hidden {
  display: none;
}

.file-input-label {
  cursor: pointer;
}

/* Current File */
.current-file {
  margin-bottom: 24px;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.file-icon {
  font-size: 1.5rem;
  color: var(--color-primary);
}

.file-details {
  flex: 1;
}

.file-name {
  font-weight: 500;
  color: var(--color-text);
  margin-bottom: 4px;
}

.file-meta {
  font-size: 0.85rem;
  color: var(--color-text-secondary);
}

/* Progress Bar */
.progress-wrapper {
  margin-top: 12px;
}

.progress-bar-container {
  height: 24px;
  background-color: var(--color-background-secondary);
  border-radius: 12px;
  overflow: hidden;
  position: relative;
}

.progress-bar-container.small {
  height: 8px;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, var(--color-primary), var(--color-primary-light));
  transition: width 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 40px;
}

.progress-text {
  color: white;
  font-size: 0.85rem;
  font-weight: 500;
}

.progress-stats {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 0.85rem;
  color: var(--color-text-secondary);
}

/* Overall Progress */
.overall-progress {
  padding: 16px;
  background-color: var(--color-background-secondary);
  border-radius: 8px;
  margin-top: 16px;
}

.overall-progress h4 {
  margin: 0 0 12px 0;
  font-size: 0.9rem;
  color: var(--color-text-secondary);
}

.files-status {
  margin-top: 8px;
  font-size: 0.85rem;
  color: var(--color-text-secondary);
}

/* Error List */
.error-list {
  margin-top: 16px;
  padding: 12px;
  background-color: rgba(var(--color-danger-rgb), 0.1);
  border-radius: 8px;
  border: 1px solid rgba(var(--color-danger-rgb), 0.2);
}

.error-list h4 {
  margin: 0 0 8px 0;
  color: var(--color-danger);
  font-size: 0.9rem;
}

.error-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 0.85rem;
  color: var(--color-danger);
}

.error-item:last-child {
  margin-bottom: 0;
}

/* Success Message */
.success-message {
  text-align: center;
  padding: 24px;
  color: var(--color-success);
}

.success-message i {
  font-size: 3rem;
  margin-bottom: 12px;
}

/* Modal Footer */
.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid var(--color-border);
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* Buttons */
.btn {
  padding: 8px 16px;
  border-radius: 6px;
  border: none;
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background-color: var(--color-primary);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: var(--color-primary-dark);
}

.btn-secondary {
  background-color: var(--color-background-secondary);
  color: var(--color-text);
}

.btn-secondary:hover:not(:disabled) {
  background-color: var(--color-background-tertiary);
}

/* Transitions */
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.3s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

.modal-fade-enter-active .modal-container,
.modal-fade-leave-active .modal-container {
  transition: transform 0.3s ease;
}

.modal-fade-enter-from .modal-container {
  transform: scale(0.9);
}

.modal-fade-leave-to .modal-container {
  transform: scale(0.9);
}

/* Responsive */
@media (max-width: 640px) {
  .modal-container {
    max-height: 90vh;
  }
  
  .modal-body {
    padding: 16px;
  }
}
</style>

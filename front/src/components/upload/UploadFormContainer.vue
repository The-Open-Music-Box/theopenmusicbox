<template>
    <div class="space-y-12 mt-20 mb-8">
        <UploadFormUI
            @files-selected="handleFileSelection"
            @submit.prevent="handleSubmit"
            :isUploading="isUploading"
        />
        <UploadProgress
            v-if="isUploading"
            :progress="uploadProgress"
        />
    </div>
</template>

<script setup lang="ts">
/**
 * UploadFormContainer Component
 *
 * Container component that orchestrates file uploading process.
 * Handles file validation, upload process, and progress tracking.
 */
import { useUnifiedUpload } from './composables/useUnifiedUpload'
import UploadFormUI from './UploadFormUI.vue'
import UploadProgress from './UploadProgress.vue'

// Define props to get the playlist ID
interface Props {
  playlistId: string
}

const props = defineProps<Props>()

// Use unified upload composable
const {
  uploadFiles,
  isUploading,
  overallProgress: uploadProgress,
  initializeFiles,
  startUpload,
  validateFile
} = useUnifiedUpload()

/**
 * Handle file selection from the form
 *
 * Validates files and adds valid files to upload queue
 * @param {FileList} files - Files selected by user
 */
const handleFileSelection = async (files: FileList) => {
    const fileArray = Array.from(files)
    // Filter valid files using the unified validation
    const validFiles = fileArray.filter(file => !validateFile(file))
    if (validFiles.length > 0) {
        initializeFiles(validFiles)
    }
}

/**
 * Handle form submission
 *
 * Initiates the upload process if files are available
 */
const handleSubmit = async () => {
    if (uploadFiles.value.length) {
        await startUpload(props.playlistId)
    }
}
</script>

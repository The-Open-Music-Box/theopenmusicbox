<template>
    <div class="space-y-12 mt-20 mb-8">
        <UploadFormUI
            @files-selected="handleFileSelection"
            @submit="handleSubmit"
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
import { useUploadValidation } from './composables/useUploadValidation'
import { useFileUpload } from './composables/useFileUpload'
import UploadFormUI from './UploadFormUI.vue'
import UploadProgress from './UploadProgress.vue'

// Use composables for validation and file uploading functionality
const { validateFiles } = useUploadValidation()
const { uploadFiles, uploadProgress, isUploading, upload } = useFileUpload()

/**
 * Handle file selection from the form
 *
 * Validates files and adds valid files to upload queue
 * @param {FileList} files - Files selected by user
 */
const handleFileSelection = async (files: FileList) => {
    const validatedFiles = await validateFiles(Array.from(files))
    if (validatedFiles.length > 0) {
        uploadFiles.value = validatedFiles
    }
}

/**
 * Handle form submission
 *
 * Initiates the upload process if files are available
 */
const handleSubmit = async () => {
    if (uploadFiles.value.length) {
        await upload()
    }
}
</script>

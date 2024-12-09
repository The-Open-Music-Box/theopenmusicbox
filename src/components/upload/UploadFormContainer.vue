// components/upload/UploadFormContainer.vue
<template>
  <div class="space-y-12 mt-20 mb-8">
    <UploadFormUI
      @files-selected="handleFileSelection"
      @submit="handleSubmit"
      :isUploading="isUploading"
    />
    <UploadProgress v-if="isUploading" :progress="uploadProgress" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useUploadValidation } from '../upload/composables/useUploadValidation'
import { useFileUpload } from '../upload/composables/useFileUpload'
import UploadFormUI from './UploadFormUI.vue'
import UploadProgress from './UploadProgress.vue'

const { validateFiles } = useUploadValidation()
const { uploadFiles, uploadProgress, isUploading, upload } = useFileUpload()

const handleFileSelection = async (files: FileList) => {
  const validatedFiles = await validateFiles(Array.from(files))
  if (validatedFiles.length > 0) {
    uploadFiles.value = validatedFiles
  }
}

const handleSubmit = async () => {
  if (uploadFiles.value.length) {
    await upload()
  }
}
</script>

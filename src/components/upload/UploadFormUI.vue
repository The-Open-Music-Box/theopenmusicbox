<template>
  <form @submit.prevent="$emit('submit')" class="space-y-12">
    <div class="border-b border-gray-900/10 pb-12">
      <div class="mt-10 grid grid-cols-1 gap-x-6 gap-y-8 sm:grid-cols-6">
        <div class="col-span-full">
          <FileDropZone @files-selected="handleFilesSelected" />
          <FileValidationMessages :errors="validationErrors" />
        </div>
      </div>
    </div>
  </form>
</template>

<script setup lang="ts">
/**
 * UploadFormUI Component
 *
 * The user interface for the file upload form.
 * Handles file selection and validation display.
 */
import { ref } from 'vue'
import FileDropZone from './FileDropZone.vue'
import FileValidationMessages from './FileValidationMessages.vue'
import { i18n } from '@/i18n'

const { t: $t } = i18n

const props = defineProps<{
  /** Whether a file upload is currently in progress */
  isUploading: boolean
}>()

/** Store validation errors from file selection */
const validationErrors = ref<string[]>([])

/**
 * Handle files selected from the drop zone
 * @param {Event} event - The file input change event
 */
const handleFilesSelected = (event: Event) => {
  const input = event.target as HTMLInputElement
  if (input.files?.length) {
    emit('files-selected', input.files)
  }
}

const emit = defineEmits<{
  /** Emitted when files are selected from the drop zone */
  (e: 'files-selected', files: FileList): void;
  /** Emitted when the form is submitted */
  (e: 'submit'): void;
}>()
</script>

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
  import { ref, defineEmits, defineProps } from 'vue'
  import FileDropZone from './FileDropZone.vue'
  import FileValidationMessages from './FileValidationMessages.vue'
  
  const props = defineProps<{
  isUploading: boolean
}>()

  const validationErrors = ref<string[]>([])
  
  const handleFilesSelected = (event: Event) => {
    const input = event.target as HTMLInputElement
    if (input.files?.length) {
      emit('files-selected', input.files)
    }
  }
  
  const emit = defineEmits<{
    (e: 'files-selected', files: FileList): void
    (e: 'submit'): void
  }>()
  </script>
  
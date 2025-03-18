// components/upload/FileDropZone.vue
<template>
  <div class="mt-2 flex justify-center rounded-lg border border-dashed border-gray-900/25 px-6 py-10">
    <div class="text-center">
      <PhotoIcon class="mx-auto h-12 w-12 text-gray-300" aria-hidden="true" />
      <div class="mt-4 flex text-sm leading-6 text-gray-600">
        <label class="relative cursor-pointer rounded-md bg-white font-semibold text-indigo-600 focus-within:outline-none focus-within:ring-2 focus-within:ring-indigo-600 focus-within:ring-offset-2 hover:text-indigo-500">
          <span>{{ $t('upload.uploadFile') }}</span>
          <input
            type="file"
            class="sr-only"
            multiple
            accept="audio/*"
            @change="$emit('filesSelected', $event)"
          />
        </label>
        <p class="pl-1">{{ $t('upload.dragDrop') }}</p>
      </div>
      <p class="text-xs leading-5 text-gray-600">{{ $t('upload.fileType') }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * FileDropZone Component
 *
 * A component that allows users to upload files by clicking or dragging and dropping.
 * Handles file input and emits selected files to the parent component.
 */
import { PhotoIcon } from '@heroicons/vue/20/solid'
import { i18n } from '@/i18n'

const { t: $t } = i18n

defineEmits<{
  /**
   * Event emitted when files are selected
   * @param event - The file input change event
   */
  (e: 'filesSelected', event: Event): void
}>()
</script>
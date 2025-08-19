<template>
  <div v-if="progress > 0" class="mt-6">
    <div class="overflow-hidden rounded-full bg-background">
      <div
        class="h-2 rounded-full bg-primary"
        :style="{ width: progress + '%' }"
      ></div>
    </div>
    <div class="mt-6 hidden grid-cols-4 text-sm font-medium text-disabled sm:grid">
      <div class="text-primary">{{ t('upload.copyingFiles') }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * UploadProgress Component
 *
 * Displays a progress bar for file uploads with status information.
 * The component visually represents the upload progress as a percentage.
 */

import { useI18n } from 'vue-i18n'

const { t } = useI18n()

defineProps<{
  /**
   * Current progress value as a percentage (0-100)
   */
  progress: number
}>()
</script>

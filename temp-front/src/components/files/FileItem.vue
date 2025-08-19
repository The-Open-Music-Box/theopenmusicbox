<template>
  <div class="flex items-center justify-between gap-x-6 py-5">
    <div class="min-w-0">
      <div class="flex items-start gap-x-3">
        <p :class="['text-onBackground', 'text-sm font-semibold leading-6']">{{ file.name }}</p>
        <FileStatus :status="file.status" />
      </div>
    </div>
    <FileActions :file="file" />
  </div>
</template>

<script setup lang="ts">
/**
 * FileItem Component
 *
 * Represents a single file in a list with its details and action buttons.
 * Shows file name, status indicator, and available actions.
 */

import FileStatus from './FileStatus.vue'
import FileActions from './FileActions.vue'
import type { LegacyAudioFile } from './types'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

defineProps<{
  /** The audio file to display */
  file: LegacyAudioFile
}>()
</script>
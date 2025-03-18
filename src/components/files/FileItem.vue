<template>
  <div class="flex items-center justify-between gap-x-6 py-5">
    <div class="min-w-0">
      <div class="flex items-start gap-x-3">
        <p class="text-sm font-semibold leading-6 text-gray-900">{{ file.name }}</p>
        <FileStatus :status="file.status" />
      </div>
    </div>
    <FileActions :file="file" />
  </div>
</template>

<script setup lang="ts">
import { defineProps } from 'vue'
import FileActions from './FileActions.vue'
import type { AudioFile } from '../files/types'

defineProps<{
  file: AudioFile
}>()
</script>
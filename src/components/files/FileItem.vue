<template>
    <div class="flex items-center justify-between gap-x-6 py-5">
      <div class="min-w-0">
        <div class="flex items-start gap-x-3">
          <p class="text-sm font-semibold leading-6 text-gray-900">{{ file.name }}</p>
          <FileStatus :status="file.status" />
        </div>
      </div>
      <FileActions :file="file" @delete="$emit('delete', file)" />
    </div>
  </template>
  
  <script setup lang="ts">
  import { defineProps, defineEmits } from 'vue'
  import FileStatus from './FileStatus.vue'
  import FileActions from './FileActions.vue'
  
  export interface AudioFile {
    id: number
    name: string
    status: string
    duration: number
    createdAt: string
  }
  
  defineProps<{
    file: AudioFile
  }>()
  
  defineEmits<{
    (e: 'delete', file: AudioFile): void
  }>()
  </script>
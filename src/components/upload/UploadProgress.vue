// components/upload/UploadProgress.vue
<template>
  <div v-if="progress > 0" class="mt-6">
    <div class="overflow-hidden rounded-full bg-gray-200">
      <div 
        class="h-2 rounded-full bg-indigo-600" 
        :style="{ width: progress + '%' }"
      />
    </div>
    <div class="mt-6 hidden grid-cols-4 text-sm font-medium text-gray-600 sm:grid">
      <div class="text-indigo-600">Copying files</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps } from 'vue'

defineProps<{
  progress: number
}>()
</script>

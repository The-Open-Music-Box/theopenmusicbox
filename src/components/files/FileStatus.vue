// components/files/FileStatus.vue
<template>
    <p :class="[STATUS_CLASSES[status], 'rounded-md whitespace-nowrap mt-0.5 px-1.5 py-0.5 text-xs font-medium ring-1 ring-inset']">
      {{ status }}
    </p>
</template>
  
<script setup lang="ts">
import { defineProps } from 'vue'
import { FileStatus, STATUS_CLASSES } from './types'

defineProps<{
  status: FileStatus
}>()
</script>
// components/files/FilesList.vue
<template>
  <ul role="list" class="divide-y divide-gray-100">
    <li v-for="file in files" :key="file.id">
      <FileItem 
        :file="file" 
      />
      
    </li>
  </ul>
</template>

<script setup lang="ts">
import { defineProps } from 'vue'
import type { AudioFile } from '../files/types'
import FileItem from './FileItem.vue'

defineProps<{
  files: AudioFile[]
}>()

</script>

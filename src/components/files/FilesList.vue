// components/files/FilesList.vue
<template>
  <ul role="list" class="divide-y divide-gray-100">
    <li v-for="file in files" :key="file.id" class="py-4">
      <div v-if="file.isAlbum" class="bg-gray-50 p-4 rounded-lg">
        <div 
          class="flex items-center justify-between cursor-pointer"
          @click="toggleAlbum(file.id)"
        >
          <div class="flex items-center">
            <svg 
              class="w-5 h-5 mr-2 transform transition-transform"
              :class="{ 'rotate-90': expandedAlbums.includes(file.id) }"
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
            <span class="font-medium">{{ file.name }}</span>
          </div>
          <span class="text-sm text-gray-500">{{ file.albumFiles?.length || 0 }} fichiers</span>
        </div>
        <div v-if="expandedAlbums.includes(file.id)" class="mt-4 pl-7">
          <ul class="space-y-2">
            <li v-for="albumFile in file.albumFiles" :key="albumFile.id">
              <FileItem :file="albumFile" />
            </li>
          </ul>
        </div>
      </div>
      <FileItem v-else :file="file" />
    </li>
  </ul>
</template>

<script setup lang="ts">
import { defineProps, ref } from 'vue'
import type { AudioFile } from '../files/types'
import FileItem from './FileItem.vue'

defineProps<{
  files: AudioFile[]
}>()

const expandedAlbums = ref<number[]>([])

const toggleAlbum = (albumId: number) => {
  const index = expandedAlbums.value.indexOf(albumId)
  if (index === -1) {
    expandedAlbums.value.push(albumId)
  } else {
    expandedAlbums.value.splice(index, 1)
  }
}
</script>

// components/files/FilesList.vue
<template>
  <div :key="componentKey">
    <p class="pl-1">List of files</p>
    <ul role="list" class="divide-y divide-gray-100">
      <li v-for="file in files" :key="file.id">
        <FileItem 
          :file="file" 
          @delete="showDeleteDialog"
        />
      </li>
    </ul>
    <DeleteDialog 
      :open="openDialogDelete" 
      :file="selectedFile" 
      @close="openDialogDelete = false"
      @confirm="deleteFile" 
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { AudioFile } from './FileItem.vue'
import FileItem from './FileItem.vue'
import DeleteDialog from '../DeleteDialog.vue'
import dataService from '../../services/dataService'

const files = ref<AudioFile[]>([])
const openDialogDelete = ref(false)
const selectedFile = ref<AudioFile | null>(null)
const componentKey = ref(0)

const loadFiles = async () => {
  try {
    files.value = await dataService.getAudioFiles()
  } catch (error) {
    console.error('Error loading files:', error)
  }
}

const showDeleteDialog = (file: AudioFile) => {
  selectedFile.value = file
  openDialogDelete.value = true
}

const deleteFile = async (file: AudioFile) => {
  try {
    await dataService.deleteFile(file.id)
    files.value = files.value.filter(f => f.id !== file.id)
    openDialogDelete.value = false
  } catch (error) {
    console.error('Error deleting file:', error)
  }
}

onMounted(loadFiles)
</script>
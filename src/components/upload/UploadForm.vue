// components/upload/UploadForm.vue
<template>
  <form @submit.prevent="handleSubmit" class="space-y-12 mt-20 mb-8">
    <div class="border-b border-gray-900/10 pb-12">
      <div class="mt-10 grid grid-cols-1 gap-x-6 gap-y-8 sm:grid-cols-6">
        <div class="col-span-full">
          <FileDropZone @filesSelected="handleFileUpload" />
        </div>
      </div>
    </div>
    <UploadProgress :progress="uploadProgress" />
  </form>
</template>

<script setup lang="ts">
import { ref, inject } from 'vue'
import FileDropZone from './FileDropZone.vue'
import UploadProgress from './UploadProgress.vue'
import api from '../../services/api'
import type { AxiosProgressEvent } from 'axios'

interface SocketService {
  emit(event: string, data: any): void;
}

const socketService = inject('socketService') as SocketService
const files = ref<File[]>([])
const uploadProgress = ref(0)


const handleFileUpload = async (event: Event) => {
  const input = event.target as HTMLInputElement
  if (!input.files?.length) return

  const audioFiles = Array.from(input.files).filter(file => file.type.startsWith('audio/'))
  if (!audioFiles.length) {
    console.warn('No audio files selected')
    return
  }

  files.value = audioFiles
}

const handleSubmit = async () => {
  if (!files.value.length) return

  const formData = new FormData()
  files.value.forEach((file, index) => {
    formData.append(`file${index}`, file)
  })

  try {
  uploadProgress.value = 0
  const response = await api.post('/api/upload', formData, {
    onUploadProgress: (progressEvent: AxiosProgressEvent) => {
      if (progressEvent.total) {
        uploadProgress.value = Math.round((progressEvent.loaded * 100) / progressEvent.total)
      }
    }
  })
    
    socketService.emit('audio_map_update', response)
    files.value = []
  } catch (error) {
    console.error('Upload error:', error)
    uploadProgress.value = 0
  }
}
</script>
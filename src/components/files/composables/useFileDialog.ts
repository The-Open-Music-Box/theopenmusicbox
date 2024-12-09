// components/files/composables/useFilesDialog.ts
import { ref } from 'vue'
import type { AudioFile } from '../types'

export function useFileDialog() {
  const showDeleteDialog = ref(false)
  const selectedFile = ref<AudioFile | null>(null)

  const openDeleteDialog = (file: AudioFile) => {
    selectedFile.value = file
    showDeleteDialog.value = true
  }

  const closeDeleteDialog = () => {
    showDeleteDialog.value = false
    selectedFile.value = null
  }

  return {
    showDeleteDialog,
    selectedFile,
    openDeleteDialog,
    closeDeleteDialog
  }
}
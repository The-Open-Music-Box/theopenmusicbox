// components/files/composables/useFilesStore.ts
import { ref } from 'vue'
import type { AudioFile, FileStatus } from '../types'
import dataService from '../../../services/dataService'

export function useFilesStore() {
  const files = ref<AudioFile[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const loadFiles = async () => {
    isLoading.value = true
    error.value = null
    try {
      files.value = await dataService.getPlaylists()
    } catch (err) {
      error.value = "Erreur lors du chargement des fichiers"
      console.error('Error loading files:', err)
    } finally {
      isLoading.value = false
    }
  }

  const deleteFile = async (id: number) => {
    try {
      await dataService.deleteFile(id)
      files.value = files.value.filter(f => f.id !== id)
    } catch (err) {
      error.value = "Erreur lors de la suppression du fichier"
      console.error('Error deleting file:', err)
      throw err // Permettre au composant de gérer l'erreur
    }
  }

  return {
    files,
    isLoading,
    error,
    loadFiles,
    deleteFile
  }
}

// components/files/composables/useFilesStore.ts
import { ref } from 'vue'
import type { PlayList, BaseContent } from '../types'
import dataService from '../../../services/dataService'

export function useFilesStore() {
  const playlists = ref<PlayList[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const loadPlaylists = async () => {
    isLoading.value = true
    error.value = null
    try {
      const data = await dataService.getPlaylists()
      console.log('Données reçues dans le store:', data)
      playlists.value = data.filter((item: BaseContent): item is PlayList => item.type === 'playlist')
      console.log('Playlists après filtrage:', playlists.value)
    } catch (err) {
      error.value = "Erreur lors du chargement des playlists"
      console.error('Error loading playlists:', err)
    } finally {
      isLoading.value = false
    }
  }

  const deleteTrack = async (playlistId: string, trackNumber: number) => {
    try {
      await dataService.deleteFile(trackNumber)
      const playlist = playlists.value.find(p => p.id === playlistId)
      if (playlist) {
        playlist.tracks = playlist.tracks.filter(t => t.number !== trackNumber)
      }
    } catch (err) {
      error.value = "Erreur lors de la suppression du morceau"
      console.error('Error deleting track:', err)
      throw err
    }
  }

  return {
    playlists,
    isLoading,
    error,
    loadPlaylists,
    deleteTrack
  }
}

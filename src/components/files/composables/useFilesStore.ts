/**
 * FilesStore Composable
 *
 * Manages the state and logic for playlists and tracks.
 * Handles loading playlists and track deletion operations.
 */
import { ref } from 'vue'
import type { PlayList, BaseContent } from '../types'
import dataService from '../../../services/dataService'
import { i18n } from '@/i18n'

export function useFilesStore() {
  const { t } = i18n
  const playlists = ref<PlayList[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  /**
   * Load all playlists from the server
   * @returns {Promise<void>}
   */
  const loadPlaylists = async () => {
    isLoading.value = true
    error.value = null
    try {
      const data = await dataService.getPlaylists()
      console.log('Data received in store:', data)
      playlists.value = data.filter((item: BaseContent): item is PlayList => item.type === 'playlist')
      console.log('Playlists after filtering:', playlists.value)
    } catch (err) {
      error.value = t('file.errorLoading')
      console.error('Error loading playlists:', err)
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Delete a track from a playlist
   * @param {string} playlistId - Playlist identifier
   * @param {number} trackNumber - Track number to delete
   * @returns {Promise<void>}
   */
  const deleteTrack = async (playlistId: string, trackNumber: number) => {
    try {
      await dataService.deleteFile(trackNumber)
      const playlist = playlists.value.find(p => p.id === playlistId)
      if (playlist) {
        playlist.tracks = playlist.tracks.filter(t => t.number !== trackNumber)
      }
    } catch (err) {
      error.value = t('file.errorDeleting')
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

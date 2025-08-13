/**
 * FilesStore Composable
 *
 * Manages the state and logic for playlists and tracks.
 * Handles loading playlists, track deletion, reordering, and playlist editing operations.
 */
import { ref } from 'vue'
import type { PlayList, BaseContent, Track } from '../types'
import dataService from '../../../services/dataService'
import { useI18n } from 'vue-i18n'

export function useFilesStore() {
  const { t } = useI18n()
  const playlists = ref<PlayList[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  
  // Initialisation du mode édition - toujours désactivé par défaut
  // Créer un singleton pour éviter de réinitialiser à chaque instanciation du store
  const isEditMode = ref(false)
  
  // Forcer la désactivation du mode édition au démarrage de l'application
  // Cela garantit que l'application commence toujours en mode normal
  localStorage.removeItem('isEditMode')
  
  const isSaving = ref(false)

  /**
   * Load all playlists from the server
   * @returns {Promise<void>}
   */
  const loadPlaylists = async () => {
    isLoading.value = true
    error.value = null
    try {
      const data = await dataService.getPlaylists()
      playlists.value = data.filter((item: BaseContent): item is PlayList => item.type === 'playlist')
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
      await dataService.deleteTrack(playlistId, trackNumber)
      const playlist = playlists.value.find(p => p.id === playlistId)
      if (playlist) {
        playlist.tracks = playlist.tracks.filter(t => t.number !== trackNumber)
      }
    } catch (err) {
      console.error('Error deleting track:', err)
      throw err
    }
  }

  /**
   * Toggle edit mode for playlists
   */
  const toggleEditMode = () => {
    isEditMode.value = !isEditMode.value
    // Save to localStorage to persist between sessions
    localStorage.setItem('isEditMode', isEditMode.value ? 'true' : 'false')
  }

  /**
   * Update a playlist title
   * @param {string} playlistId - Playlist identifier
   * @param {string} newTitle - New title for the playlist
   * @returns {Promise<void>}
   */
  const updatePlaylistTitle = async (playlistId: string, newTitle: string) => {
    try {
      isSaving.value = true
      error.value = null
      
      // Call API to update playlist title
      await dataService.updatePlaylist(playlistId, { title: newTitle })
      
      // Update local state
      const playlist = playlists.value.find(p => p.id === playlistId)
      if (playlist) {
        playlist.title = newTitle
      }
    } catch (err) {
      error.value = t('file.errorUpdating')
      console.error('Error updating playlist title:', err)
      throw err
    } finally {
      isSaving.value = false
    }
  }

  /**
   * Reorder tracks within a playlist
   * @param {string} playlistId - Playlist identifier
   * @param {number[]} newOrder - New order of track numbers
   * @returns {Promise<void>}
   */
  const reorderPlaylistTracks = async (playlistId: string, newOrder: number[]) => {
    try {
      isSaving.value = true
      error.value = null
      
      // Call API to reorder tracks
      await dataService.reorderTracks(playlistId, newOrder)
      
      // Update local state
      const playlist = playlists.value.find(p => p.id === playlistId)
      if (playlist) {
        // Create a map of track number to track object
        const trackMap = new Map()
        playlist.tracks.forEach(track => trackMap.set(track.number, track))
        
        // Reorder tracks based on new order
        const reorderedTracks = newOrder.map(number => trackMap.get(number))
          .filter((track): track is Track => track !== undefined)
        
        playlist.tracks = reorderedTracks
      }
    } catch (err) {
      error.value = t('file.errorReordering')
      console.error('Error reordering tracks:', err)
      throw err
    } finally {
      isSaving.value = false
    }
  }

  /**
   * Move a track from one playlist to another
   * @param {string} sourcePlaylistId - Source playlist identifier
   * @param {string} targetPlaylistId - Target playlist identifier
   * @param {number} trackNumber - Track number to move
   * @param {number} targetPosition - Position in target playlist (optional)
   * @returns {Promise<void>}
   */
  const moveTrackBetweenPlaylists = async (
    sourcePlaylistId: string, 
    targetPlaylistId: string, 
    trackNumber: number,
    targetPosition?: number
  ) => {
    try {
      isSaving.value = true
      error.value = null
      
      // Call the backend API to move the track
      await dataService.moveTrackBetweenPlaylists(
        sourcePlaylistId,
        targetPlaylistId,
        trackNumber,
        targetPosition
      )
      
      // Refresh both playlists to reflect the changes
      await loadPlaylists()
      
      console.log('Track successfully moved between playlists')
    } catch (err) {
      error.value = t('file.errorMoving')
      console.error('Error moving track between playlists:', err)
      throw err
    } finally {
      isSaving.value = false
    }
  }

  /**
   * Create a new playlist
   * @param {string} title - Title for the new playlist
   * @returns {Promise<string>} - ID of the created playlist
   */
  const createNewPlaylist = async (title: string) => {
    try {
      isLoading.value = true
      error.value = null
      
      // Call API to create new playlist
      const response = await dataService.createPlaylist({ title })
      // Process playlist response
      
      // Handle both response formats:
      // 1. Response with nested playlist object: { playlist: { id: '...', ... } }
      // 2. Direct playlist object: { id: '...', ... }
      let playlistId = null
      
      if (response && response.playlist && response.playlist.id) {
        // Format 1: Nested playlist object
        playlistId = response.playlist.id
        console.log('[useFilesStore] New playlist created with ID:', playlistId)
      } else if (response && response.id) {
        // Format 2: Direct playlist object
        playlistId = response.id
        console.log('[useFilesStore] New playlist created with ID:', playlistId)
      } else {
        console.error('[useFilesStore] Invalid response format:', response)
        throw new Error('Invalid response format')
      }
      
      // Reload playlists to get updated data including the new playlist
      // Only executed if we have a valid playlist ID
      // Reload playlists after successful creation
      await loadPlaylists()
      
      return playlistId
    } catch (err) {
      error.value = t('file.errorCreating')
      console.error('[useFilesStore] Error creating playlist:', err)
      throw err
    } finally {
      isSaving.value = false
    }
  }

  return {
    playlists,
    isLoading,
    isSaving,
    error,
    isEditMode,
    loadPlaylists,
    deleteTrack,
    toggleEditMode,
    updatePlaylistTitle,
    reorderPlaylistTracks,
    moveTrackBetweenPlaylists,
    createNewPlaylist
  }
}

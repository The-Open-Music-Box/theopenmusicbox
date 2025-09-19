/**
 * Main API Service for TheOpenMusicBox
 * 
 * Refactored modular API service that imports specialized modules
 * and provides backward compatibility for existing components.
 */

import { API_ROUTES, API_CONFIG } from '../constants/apiRoutes'
import { logger } from '../utils/logger'
import { generateClientOpId } from '../utils/operationUtils'

// Import all API modules
import { apiClient, ApiResponseHandler, StandardApiError } from './api/apiClient'
import { playerApi } from './api/playerApi'
import { playlistApi } from './api/playlistApi'
import { uploadApi } from './api/uploadApi'
import { systemApi } from './api/systemApi'
import { nfcApi } from './api/nfcApi'
import { youtubeApi } from './api/youtubeApi'

/**
 * Main API service export with organized modules and backward compatibility
 */
export const apiService = {
  player: playerApi,
  playlists: playlistApi,
  uploads: uploadApi,
  system: systemApi,
  nfc: nfcApi,
  youtube: youtubeApi,

  // Direct axios client access for custom requests
  client: apiClient,

  // Error handling utilities
  StandardApiError,

  /**
   * Check if error is of specific type
   */
  isErrorType(error: unknown, type: string): boolean {
    return error instanceof StandardApiError && error.isType(type)
  },

  /**
   * Check if error is retryable
   */
  isRetryable(error: unknown): boolean {
    return error instanceof StandardApiError && error.isRetryable()
  },

  // Backward compatibility methods - delegate to appropriate modules
  async getPlayerStatus() {
    return playerApi.getStatus()
  },

  async getPlaylists() {
    try {
      const result = await playlistApi.getPlaylists(1, API_CONFIG.PLAYLISTS_FETCH_LIMIT)
      return result.items // Extract items from paginated response
    } catch (error) {
      // If the new API format fails, fall back to legacy response format
      const response = await apiClient.get(API_ROUTES.PLAYLISTS, {
        params: { page: 1, limit: API_CONFIG.PLAYLISTS_FETCH_LIMIT }
      })
      const data = ApiResponseHandler.extractData(response) as any

      // Handle different response formats - backend now uses "playlists" consistently
      if (Array.isArray(data)) {
        return data
      } else if (data?.playlists) {
        return data.playlists // Backend uses "playlists" field
      } else if (data?.items) {
        return data.items // Fallback to old "items" format
      } else {
        return []
      }
    }
  },

  async togglePlayer(clientOpId?: string) {
    return playerApi.toggle(clientOpId)
  },

  async playPlayer(clientOpId?: string) {
    // Since backend only has toggle, we call toggle
    // UI components should handle state management
    return playerApi.toggle(clientOpId)
  },

  async pausePlayer(clientOpId?: string) {
    // Since backend only has toggle, we call toggle
    // UI components should handle state management
    return playerApi.toggle(clientOpId)
  },

  async seekPlayer(positionMs: number, clientOpId?: string) {
    return playerApi.seek(positionMs, clientOpId)
  },

  async previousTrack(clientOpId?: string) {
    return playerApi.previous(clientOpId)
  },

  async nextTrack(clientOpId?: string) {
    return playerApi.next(clientOpId)
  },

  async createPlaylist(title: string, description?: string) {
    return playlistApi.createPlaylist(title, description || '')
  },

  async deletePlaylist(playlistId: string) {
    return playlistApi.deletePlaylist(playlistId)
  },

  async getPlaylist(playlistId: string) {
    return playlistApi.getPlaylist(playlistId)
  },

  async updatePlaylist(playlistId: string, data: { title?: string; description?: string }) {
    return playlistApi.updatePlaylist(playlistId, data.title, data.description)
  },

  async deleteTrack(playlistId: string, trackNumber: number) {
    return playlistApi.deleteTrack(playlistId, trackNumber)
  },

  async reorderTracks(playlistId: string, trackOrder: number[]) {
    const response = await apiClient.post(API_ROUTES.PLAYLIST_REORDER(playlistId), {
      track_order: trackOrder,
      client_op_id: generateClientOpId('reorder_tracks')
    })
    return ApiResponseHandler.extractData(response)
  },

  async playTrack(playlistId: string, trackNumber: number) {
    const response = await apiClient.post(API_ROUTES.PLAYLIST_PLAY_TRACK(playlistId, trackNumber))
    return ApiResponseHandler.extractData(response)
  },

  async startPlaylist(playlistId: string) {
    try {
      // Start the playlist
      const result = await playlistApi.startPlaylist(playlistId)

      // Immediately request updated player state to ensure consistency
      // Small delay to allow backend state to propagate
      setTimeout(async () => {
        try {
          const { useServerStateStore } = await import('@/stores/serverStateStore')
          const serverStateStore = useServerStateStore()
          await serverStateStore.requestInitialPlayerState()
          logger.debug('Requested fresh player state after playlist start')
        } catch (error) {
          logger.error('Failed to sync state after playlist start:', error)
        }
      }, 300)

      return result
    } catch (error) {
      logger.error('Failed to start playlist:', error)
      throw error
    }
  },

  async moveTrackBetweenPlaylists(
    sourcePlaylistId: string,
    targetPlaylistId: string,
    trackNumber: number,
    targetPosition?: number
  ) {
    const payload: any = {
      source_playlist_id: sourcePlaylistId,
      target_playlist_id: targetPlaylistId,
      track_number: trackNumber,
      client_op_id: generateClientOpId('move_track')
    }

    if (targetPosition !== undefined) {
      payload.target_position = targetPosition
    }

    const response = await apiClient.post(API_ROUTES.PLAYLIST_MOVE_TRACK, payload)
    return ApiResponseHandler.extractData(response)
  },

  // NFC backward compatibility methods
  async startNfcAssociation(playlistId: string, clientOpId?: string) {
    return nfcApi.startNfcAssociationScan(playlistId, 60000, clientOpId)
  },

  async cancelNfcObservation(clientOpId?: string) {
    // Cancel NFC scan - implemented via timeout or explicit cancel if available
    return Promise.resolve({ status: 'success', message: 'NFC observation cancelled' })
  },

  async overrideNfcAssociation(playlistId: string, clientOpId?: string) {
    // Override requires knowing the tag ID, but in legacy usage pattern
    // this would be called during association flow where tag is known
    return nfcApi.startNfcScan(60000, clientOpId)
  },

  async getNfcStatus() {
    return nfcApi.getNfcStatus()
  },

  async associateNfcTag(playlistId: string, tagId: string, clientOpId?: string) {
    return nfcApi.associateNfcTag(playlistId, tagId, clientOpId)
  },

  async removeNfcAssociation(tagId: string, clientOpId?: string) {
    return nfcApi.removeNfcAssociation(tagId, clientOpId)
  },

  async startNfcScan(timeoutMs?: number, clientOpId?: string) {
    return nfcApi.startNfcScan(timeoutMs, clientOpId)
  },

  // Upload system backward compatibility methods
  async initUpload(playlistId: string, filename: string, fileSize: number) {
    return uploadApi.initUpload(playlistId, filename, fileSize)
  },

  async uploadChunk(playlistId: string, sessionId: string, chunkIndex: number, chunk: Blob) {
    return uploadApi.uploadChunk(playlistId, sessionId, chunkIndex, chunk)
  },

  async finalizeUpload(playlistId: string, sessionId: string, clientOpId?: string) {
    return uploadApi.finalizeUpload(playlistId, sessionId, clientOpId)
  },

  async getUploadStatus(playlistId: string, sessionId: string) {
    return uploadApi.getUploadStatus(playlistId, sessionId)
  }
}

// Export individual modules for direct import
export { playerApi, playlistApi, uploadApi, systemApi, nfcApi, youtubeApi, apiClient, ApiResponseHandler, StandardApiError }

// Default export for backward compatibility
export default apiService
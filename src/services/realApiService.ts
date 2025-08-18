/**
 * Real API Service
 * Provides production-ready HTTP client for communication with the backend API.
 * Features include request/response interceptors, caching, error handling, and retry logic.
 *
 * IMPORTANT: All routes in this service are aligned with the backend API documentation
 * found in /back/routes-api.md
 */

import axios, { AxiosError, InternalAxiosRequestConfig, AxiosResponse, AxiosProgressEvent } from 'axios'
import { API_ROUTES } from '../constants/apiRoutes'
import logger from '../utils/logger'

const apiBaseUrl = window.location.origin;

/**
 * Configured axios instance for making API requests
 * Includes base URL, timeout settings, and default headers
 */
const apiClient = axios.create({
  baseURL: apiBaseUrl,
  timeout: 60000,
  headers: {
    Accept: 'application/json'
  }
})

/**
 * Import centralized cache service
 */
import cacheService from './cacheService'


// SystemHealth interface removed as it's not used in the current implementation

/**
 * Metrics collection for API performance monitoring
 */
const metrics = {
  requestCount: 0,
  errorCount: 0,
  averageResponseTime: 0
}

declare module 'axios' {
  export interface InternalAxiosRequestConfig {
    metadata?: {
      start: number
    }
  }
}

/**
 * Implements retry logic for failed requests
 * @param error - The axios error from the failed request
 * @param retries - Number of retry attempts remaining (default: 3)
 * @param delay - Milliseconds to wait between retries (default: 1000)
 * @returns Promise resolving to the axios response if retry succeeds
 * @private
 */
const retryRequest = async (error: AxiosError, retries = 3, delay = 1000): Promise<AxiosResponse> => {
  const config = error.config
  if (!config || !retries) {
    return Promise.reject(error)
  }

  await new Promise(resolve => setTimeout(resolve, delay))
  return apiClient(config)
}

// Request interceptor - adds timestamp metadata to track request duration
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  config.metadata = { start: Date.now() }
  return config
})

// Response interceptor - handles metrics and implements retry logic for server errors
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    const duration = Date.now() - (response.config.metadata?.start || 0)
    metrics.requestCount++
    metrics.averageResponseTime = (metrics.averageResponseTime * (metrics.requestCount - 1) + duration) / metrics.requestCount
    return response
  },
  async (error: AxiosError) => {
    metrics.errorCount++

    if (error.response?.status && error.response.status >= 500) {
      try {
        return await retryRequest(error)
      } catch (retryError) {
        return Promise.reject(retryError)
      }
    }

    return Promise.reject(error)
  }
)

/**
 * Production API service implementation
 * Provides methods for interacting with the backend API endpoints
 */
class RealApiService {
  /**
   * Fetch all playlists
   * @returns Promise resolving to array of playlists
   */
  async getPlaylists() {
    try {
      const response = await apiClient.get(API_ROUTES.PLAYLISTS)
      if (response.data === null || response.data === undefined) {
        throw new Error('API response.data is null or undefined')
      }

      // Check if response.data.playlists is an array (even if empty)
      if (!Array.isArray(response.data.playlists)) {
        throw new Error('API response.data.playlists is not an array')
      }

      return response.data.playlists
    } catch (error) {
      logger.error('Error fetching playlists', error, 'RealApiService')
      throw error
    }
  }

  /**
   * Get details for a specific playlist
   * @param playlistId - ID of the playlist
   * @returns Promise resolving to playlist object
   */
  async getPlaylist(playlistId: string) {
    try {
      const response = await apiClient.get(API_ROUTES.PLAYLIST(playlistId))
      return response.data
    } catch (error) {
      logger.error('Error fetching playlist', error, 'RealApiService')
      throw error
    }
  }

  /**
   * Create a new playlist
   * @param playlistData - Playlist data object
   * @returns Promise resolving to created playlist
   */
  async createPlaylist(playlistData: { title: string }) {
    try {
      // Force the correct structure with title property
      const payload = { title: playlistData.title || 'New Playlist' }

      // Debug logs for playlist creation
      logger.debug('Creating playlist with raw data', playlistData, 'RealApiService')
      logger.debug('Normalized payload', payload, 'RealApiService')
      logger.debug('API route', { route: API_ROUTES.PLAYLISTS, fullUrl: apiBaseUrl + API_ROUTES.PLAYLISTS }, 'RealApiService')

      // Make POST request to create playlist
      const response = await apiClient.post(API_ROUTES.PLAYLISTS, payload)
      logger.debug('Create playlist response', { status: response.status, data: response.data }, 'RealApiService')
      return response.data
    } catch (error: unknown) {
      const axiosError = error as AxiosError;
      logger.error('Error creating playlist', {
        message: axiosError.message,
        status: axiosError.response?.status,
        data: axiosError.response?.data,
        hasRequest: !!axiosError.request
      }, 'RealApiService')
      throw error
    }
  }

  /**
   * Delete a playlist
   * @param playlistId - ID of the playlist
   * @returns Promise resolving to server response
   */
  async deletePlaylist(playlistId: string) {
    try {
      const response = await apiClient.delete(API_ROUTES.PLAYLIST(playlistId))
      return response.data
    } catch (error) {
      logger.error('Error deleting playlist', error, 'RealApiService')
      throw error
    }
  }

  /**
   * Update a playlist
   * @param playlistId - ID of the playlist
   * @param playlistData - Updated playlist data
   * @returns Promise resolving to updated playlist
   */
  async updatePlaylist(playlistId: string, playlistData: { title?: string; [key: string]: unknown }) {
    try {
      logger.debug(`Calling API: PUT ${API_ROUTES.PLAYLIST(playlistId)}`, playlistData, 'RealApiService')
      const response = await apiClient.put(API_ROUTES.PLAYLIST(playlistId), playlistData)
      logger.debug('API response', response.data, 'RealApiService')
      return response.data
    } catch (error) {
      logger.error('Error updating playlist', error, 'RealApiService')
      throw error
    }
  }

  /**
   * Uploads files to a playlist (legacy method)
   * @param playlistId - ID of the playlist
   * @param files - Files to upload
   * @param onUploadProgress - Optional callback for upload progress
   * @returns Promise resolving to upload result
   * @deprecated Use initUpload, uploadChunk, and finalizeUpload instead
   */
  async uploadFiles(playlistId: string, files: FileList | File[], onUploadProgress?: (progressEvent: AxiosProgressEvent) => void) {
    const formData = new FormData()

    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i])
    }

    const response = await apiClient.post(API_ROUTES.PLAYLIST_UPLOAD(playlistId), formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress
    })

    return response.data
  }

  /**
   * Initializes a chunked upload session
   * @param playlistId - ID of the playlist
   * @param metadata - File metadata (filename, file_size)
   * @returns Promise resolving to session initialization data
   */
  async initUpload(playlistId: string, metadata: { filename: string, file_size: number }) {
    try {
      const response = await apiClient.post(
        API_ROUTES.PLAYLIST_UPLOAD_SESSION(playlistId),
        metadata
      )
      return response.data
    } catch (error) {
      logger.error('Error initializing upload', error, 'RealApiService')
      throw error
    }
  }

  /**
   * Uploads a single chunk of a file
   * @param playlistId - ID of the playlist
   * @param formData - FormData containing session_id, chunk_index, and file chunk
   * @returns Promise resolving to chunk upload result
   */
  async uploadChunk(playlistId: string, sessionId: string, chunkIndex: number, formData: FormData) {
    try {
      const response = await apiClient.post(
        API_ROUTES.PLAYLIST_UPLOAD_CHUNK(playlistId, sessionId, chunkIndex),
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' }
        }
      )
      return response.data
    } catch (error) {
      logger.error('Error uploading chunk', error, 'RealApiService')
      throw error
    }
  }

  /**
   * Finalizes a chunked upload session
   * @param playlistId - ID of the playlist
   * @param data - Session data for finalization
   * @returns Promise resolving to finalization result
   */
  async finalizeUpload(playlistId: string, data: { session_id: string }) {
    try {
      const response = await apiClient.post(
        API_ROUTES.PLAYLIST_UPLOAD_FINALIZE(playlistId, data.session_id),
        data
      )
      return response.data
    } catch (error) {
      logger.error('Error finalizing upload', error, 'RealApiService')
      throw error
    }
  }

  /**
   * Gets the status of an upload session
   * @param sessionId - ID of the upload session
   * @returns Promise resolving to session status
   */
  async getUploadStatus(playlistId: string, sessionId: string) {
    try {
      const response = await apiClient.get(
        API_ROUTES.PLAYLIST_UPLOAD_STATUS(playlistId, sessionId)
      )
      return response.data
    } catch (error) {
      logger.error('Error getting upload status', error, 'RealApiService')
      throw error
    }
  }

  /**
   * Reorder tracks in a playlist
   * @param playlistId - ID of the playlist
   * @param trackOrder - Array of track numbers in new order
   * @returns Promise resolving to server response
   */
  async reorderTracks(playlistId: string, trackOrder: number[]) {
    try {
      const response = await apiClient.post(API_ROUTES.PLAYLIST_REORDER(playlistId), { track_order: trackOrder })
      return response.data
    } catch (error) {
      logger.error('Error reordering tracks', error, 'RealApiService')
      throw error
    }
  }

  /**
   * Play a specific track in a playlist
   * @param playlistId - ID of the playlist
   * @param trackNumber - Number of the track to play
   * @returns Promise resolving to server response
   */
  async playTrack(playlistId: string, trackNumber: number) {
    try {
      const response = await apiClient.post(API_ROUTES.PLAYLIST_TRACK(playlistId, trackNumber))
      return response.data
    } catch (error) {
      logger.error('Error playing track', error, 'RealApiService')
      throw error
    }
  }

  /**
   * Delete a track from a playlist
   * @param playlistId - ID of the playlist
   * @param trackNumber - Number of the track
   * @returns Promise resolving to server response
   */
  async deleteTrack(playlistId: string, trackNumber: number) {
    try {
      const response = await apiClient.delete(`/api/playlists/${playlistId}/tracks`, {
        data: { track_numbers: [trackNumber] },
        headers: { 'Content-Type': 'application/json' }
      })
      return response.data
    } catch (error) {
      logger.error('Error deleting track', error, 'RealApiService')
      throw error
    }
  }

  /**
   * Delete multiple tracks from a playlist
   * @param playlistId - ID of the playlist
   * @param trackIds - Array of track IDs
   * @returns Promise resolving to server response
   */
  async deleteTracks(playlistId: string, trackIds: string[] | number[]) {
    try {
      const response = await apiClient.delete(`/api/playlists/${playlistId}/tracks`, { 
        data: { track_numbers: trackIds },
        headers: { 'Content-Type': 'application/json' }
      })
      return response.data
    } catch (error) {
      logger.error('Error deleting tracks', error, 'RealApiService')
      throw error
    }
  }

  /**
   * Start playlist playback
   * @param playlistId - ID of the playlist
   * @returns Promise resolving to server response
   */
  async startPlaylist(playlistId: string) {
    try {
      const response = await apiClient.post(API_ROUTES.PLAYBACK_START(playlistId))
      logger.debug('Start playlist response', response.data, 'RealApiService')
      return response.data
    } catch (error) {
      logger.error('Error starting playlist', error, 'RealApiService')
      throw error
    }
  }

  /**
   * Control playlist playback (pause, resume, stop, next, previous, etc)
   * @param action - Action string (pause, resume, stop, next, previous, ...)
   * @returns Promise resolving to server response
   */
  async controlPlaylist(action: string) {
    try {
      const response = await apiClient.post(API_ROUTES.PLAYBACK_CONTROL, { action })
      return response.data;
    } catch (error) {
      logger.error('Error controlling playlist', error, 'RealApiService');
      throw error;
    }
  }

  /**
   * Get current playback status
   * @returns Promise resolving to playback status
   */
  async getPlaybackStatus() {
    try {
      const response = await apiClient.get(API_ROUTES.PLAYBACK_STATUS)
      return response.data
    } catch (error) {
      logger.error('Error getting playback status', error, 'RealApiService')
      throw error
    }
  }

  // YouTube methods

  /**
   * Download YouTube audio
   * @param url - YouTube URL
   * @returns Promise resolving to download status
   */
  async downloadYouTube(url: string) {
    try {
      const response = await apiClient.post(API_ROUTES.YOUTUBE_DOWNLOAD, { url })
      return response.data
    } catch (error) {
      logger.error('Error downloading YouTube audio', error, 'RealApiService')
      throw error
    }
  }

  // Health

  /**
   * Check system health
   * @returns Promise resolving to health status
   */
  async checkHealth() {
    try {
      const response = await apiClient.get(API_ROUTES.SYSTEM_INFO)
      return response.data
    } catch (error) {
      logger.error('Error fetching health status', error, 'RealApiService')
      throw error
    }
  }

  /**
   * Get current system volume
   * @returns Promise resolving to volume level (0-100)
   */
  async getVolume() {
    try {
      const response = await apiClient.get(API_ROUTES.VOLUME)
      return response.data
    } catch (error) {
      logger.error('Error getting volume', error, 'RealApiService')
      throw error
    }
  }

  /**
   * Set system volume
   * @param volume - Volume level (0-100)
   * @returns Promise resolving to server response
   */
  async setVolume(volume: number) {
    try {
      if (volume < 0 || volume > 100) {
        throw new Error('Volume must be between 0 and 100')
      }
      const response = await apiClient.post(API_ROUTES.VOLUME, { volume })
      return response.data
    } catch (error) {
      logger.error('Error setting volume', error, 'RealApiService')
      throw error
    }
  }

  /**
   * Fetches the list of audio files from the server
   * Implements caching to avoid redundant requests
   * @returns Promise resolving to the list of audio files
   */
  async getAudioFiles() {
    const cacheKey = 'audio_files'
    const cachedData = cacheService.get(cacheKey)
    if (cachedData) {
      return cachedData
    }
    try {
      logger.debug('Fetching audio files from API', undefined, 'RealApiService')
      const response = await apiClient.get('/api/nfc_mapping')
      logger.debug('Audio files response', response.data, 'RealApiService')

      const playlists = response.data
      logger.debug('Transformed playlists', playlists, 'RealApiService')

      cacheService.set(cacheKey, playlists)
      return playlists
    } catch (err) {
      const error = err as AxiosError
      logger.error('Error fetching audio files', {
        response: error.response?.data,
        status: error.response?.status,
        headers: error.response?.headers
      }, 'RealApiService')
      if (error.response?.status === 401) {
        // Gérer l'authentification
      } else if (error.response?.status === 503) {
        // Gérer la maintenance
      }
      throw error
    }
  }

  /**
   * Requests a new upload session ID from the server
   * Used for tracking multi-part or chunked uploads
   * @returns Promise resolving to the session ID string
   */
  async getUploadSessionId(): Promise<string> {
    try {
      const response = await apiClient.post('/api/uploads/session', {});
      return response.data.session_id;
    } catch (error) {
      logger.error('Error getting upload session ID', error, 'RealApiService')
      throw error
    }
  }

  /**
   * Downloads a file from the server
   * @param fileId - ID of the file to download
   * @param onProgress - Optional callback for tracking download progress
   * @returns Promise resolving to the file blob
   */
  async downloadFile(fileId: number, onProgress?: (progress: number) => void): Promise<Blob> {
    const response = await apiClient.get(`/api/files/${fileId}/download`, {
      responseType: 'blob',
      onDownloadProgress: (progressEvent: AxiosProgressEvent) => {
        if (onProgress && progressEvent.total) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(percent);
        }
      }
    });
    return response.data;
  }

  /**
   * Generates a download URL for a file
   * @param fileId - ID of the file
   * @returns URL string for downloading the file
   */
  downloadFileUrl(fileId: number): string {
    return `${apiBaseUrl}/api/files/${fileId}/download`;
  }

  /**
   * Associate an NFC tag with a playlist
   * @param nfcTagId - NFC tag identifier
   * @param playlistId - Playlist identifier
   * @returns Promise resolving to association status
   */
  async associateNfcTag(nfcTagId: string, playlistId: string) {
    try {
      const response = await apiClient.post(API_ROUTES.NFC_ASSOCIATE(nfcTagId, playlistId))
      return response.data
    } catch (error) {
      logger.error('Error associating NFC tag', error, 'RealApiService')
      throw error
    }
  }

  /**
   * Remove NFC association from a playlist
   * @param playlistId - Playlist identifier
   * @returns Promise resolving to removal status
   */
  async removeNfcAssociation(playlistId: string) {
    try {
      const response = await apiClient.delete(API_ROUTES.NFC_REMOVE_ASSOCIATION(playlistId))
      return response.data
    } catch (error) {
      logger.error('Error removing NFC association', error, 'RealApiService')
      throw error
    }
  }

  /**
   * Get playlist associated with an NFC tag
   * @param nfcTagId - NFC tag identifier
   * @returns Promise resolving to associated playlist
   */
  async getNfcPlaylist(nfcTagId: string) {
    try {
      const response = await apiClient.get(API_ROUTES.NFC_GET_PLAYLIST(nfcTagId))
      return response.data
    } catch (error) {
      logger.error('Error getting NFC playlist', error, 'RealApiService')
      throw error
    }
  }

  /**
   * Scan for available NFC tags
   * @returns Promise resolving to scan results
   */
  async scanNfcTags() {
    try {
      const response = await apiClient.get(API_ROUTES.NFC_SCAN)
      return response.data
    } catch (error) {
      logger.error('Error scanning NFC tags', error, 'RealApiService')
      throw error
    }
  }

  /**
   * Write data to an NFC tag
   * @param tagId - NFC tag identifier
   * @param data - Data to write to the tag
   * @returns Promise resolving to write status
   */
  async writeNfcTag(tagId: string, data: string) {
    try {
      const response = await apiClient.post(API_ROUTES.NFC_WRITE, { tag_id: tagId, data })
      return response.data
    } catch (error) {
      logger.error('Error writing NFC tag', error, 'RealApiService')
      throw error
    }
  }

  /**
   * Retrieves current NFC status
   * @returns Promise resolving to NFC status data
   */
  async getNfcStatus() {
    try {
      const response = await apiClient.get(API_ROUTES.NFC_STATUS)
      return response.data
    } catch (error) {
      logger.error('Error getting NFC status', error, 'RealApiService')
      throw error
    }
  }

  /**
   * Search YouTube videos
   * @param query - Search query
   * @param maxResults - Maximum number of results (optional)
   * @returns Promise resolving to search results
   */
  async searchYouTube(query: string, maxResults?: number) {
    try {
      const params = new URLSearchParams({ query })
      if (maxResults) {
        params.append('max_results', maxResults.toString())
      }
      const response = await apiClient.get(`${API_ROUTES.YOUTUBE_SEARCH}?${params}`)
      return response.data
    } catch (error) {
      logger.error('Error searching YouTube', error, 'RealApiService')
      throw error
    }
  }

  /**
   * Get YouTube download task status
   * @param taskId - Task identifier
   * @returns Promise resolving to task status
   */
  async getYouTubeStatus(taskId: string) {
    try {
      const response = await apiClient.get(API_ROUTES.YOUTUBE_STATUS(taskId))
      return response.data
    } catch (error) {
      logger.error('Error getting YouTube status', error, 'RealApiService')
      throw error
    }
  }

  /**
   * Get system information
   * @returns Promise resolving to system info
   */
  async getSystemInfo() {
    try {
      const response = await apiClient.get(API_ROUTES.SYSTEM_INFO)
      return response.data
    } catch (error) {
      logger.error('Error getting system info', error, 'RealApiService')
      throw error
    }
  }

  /**
   * Get system logs
   * @returns Promise resolving to system logs
   */
  async getSystemLogs() {
    try {
      const response = await apiClient.get(API_ROUTES.SYSTEM_LOGS)
      return response.data
    } catch (error) {
      logger.error('Error getting system logs', error, 'RealApiService')
      throw error
    }
  }

  /**
   * Restart the system
   * @returns Promise resolving to restart status
   */
  async restartSystem() {
    try {
      const response = await apiClient.post(API_ROUTES.SYSTEM_RESTART)
      return response.data
    } catch (error) {
      logger.error('Error restarting system', error, 'RealApiService')
      throw error
    }
  }

  /**
   * Sync playlists with filesystem
   * @returns Promise resolving to sync status
   */
  async syncPlaylists() {
    try {
      const response = await apiClient.post(API_ROUTES.PLAYLIST_SYNC)
      return response.data
    } catch (error) {
      logger.error('Error syncing playlists', error, 'RealApiService')
      throw error
    }
  }

  /**
   * Move a track from one playlist to another
   * @param sourcePlaylistId - Source playlist identifier
   * @param targetPlaylistId - Target playlist identifier
   * @param trackNumber - Track number to move
   * @param targetPosition - Position in target playlist (optional)
   * @returns Promise resolving to move operation result
   */
  async moveTrackBetweenPlaylists(
    sourcePlaylistId: string,
    targetPlaylistId: string,
    trackNumber: number,
    targetPosition?: number
  ) {
    try {
      const payload: {
        source_playlist_id: string;
        target_playlist_id: string;
        track_number: number;
        target_position?: number;
      } = {
        source_playlist_id: sourcePlaylistId,
        target_playlist_id: targetPlaylistId,
        track_number: trackNumber
      }
      
      if (targetPosition !== undefined) {
        payload.target_position = targetPosition
      }

      const response = await apiClient.post('/api/playlists/move-track', payload)
      return response.data
    } catch (error) {
      logger.error('Error moving track between playlists', error, 'RealApiService')
      throw error
    }
  }
}

export default new RealApiService()

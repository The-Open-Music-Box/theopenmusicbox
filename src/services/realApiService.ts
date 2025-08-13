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

const apiBaseUrl = window.location.origin;

/**
 * Configured axios instance for making API requests
 * Includes base URL, timeout settings, and default headers
 */
const apiClient = axios.create({
  baseURL: apiBaseUrl,
  timeout: 60000,
  headers: {
    Accept: 'application/json',
    'Content-Type': 'application/json'
  }
})

/**
 * In-memory cache for API responses to avoid redundant network requests
 */
const cache = new Map()

interface ComponentHealth {
  status: string
  timestamp: number
}

interface SystemHealth {
  components: {
    [key: string]: ComponentHealth
  }
  status: string
  timestamp: number
}

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
      console.error('Error fetching playlists:', error)
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
      console.error('Error fetching playlist:', error)
      throw error
    }
  }

  /**
   * Create a new playlist
   * @param playlistData - Playlist data object
   * @returns Promise resolving to created playlist
   */
  async createPlaylist(playlistData: any) {
    try {
      // Force the correct structure with title property
      const payload = { title: playlistData.title || 'New Playlist' }

      // Logs détaillés pour le débogage
      console.log('[realApiService] Creating playlist with raw data:', playlistData)
      console.log('[realApiService] Normalized payload:', payload)
      console.log('[realApiService] API_ROUTES.PLAYLISTS =', API_ROUTES.PLAYLISTS)
      console.log('[realApiService] Full URL =', apiBaseUrl + API_ROUTES.PLAYLISTS)
      console.log('[realApiService] Headers =', apiClient.defaults.headers)

      // Make POST request to create playlist
      const response = await apiClient.post(API_ROUTES.PLAYLISTS, payload)
      console.log('[realApiService] Create playlist response status:', response.status)
      console.log('[realApiService] Create playlist response data:', response.data)
      return response.data
    } catch (error: any) {
      console.error('[realApiService] Error creating playlist:', error)
      if (error.response) {
        console.error('[realApiService] Error response status:', error.response.status)
        console.error('[realApiService] Error response data:', error.response.data)
        console.error('[realApiService] Error response headers:', error.response.headers)
      } else if (error.request) {
        console.error('[realApiService] Error request:', error.request)
      } else {
        console.error('[realApiService] Error message:', error.message)
      }
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
      console.error('Error deleting playlist:', error)
      throw error
    }
  }

  /**
   * Update a playlist
   * @param playlistId - ID of the playlist
   * @param playlistData - Updated playlist data
   * @returns Promise resolving to updated playlist
   */
  async updatePlaylist(playlistId: string, playlistData: any) {
    try {
      console.debug(`Calling API: PUT ${API_ROUTES.PLAYLIST(playlistId)}`, playlistData)
      const response = await apiClient.put(API_ROUTES.PLAYLIST(playlistId), playlistData)
      console.debug('API response:', response.data)
      return response.data
    } catch (error) {
      console.error('Error updating playlist:', error)
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
   * @param metadata - File metadata (filename, size, chunks)
   * @returns Promise resolving to session initialization data
   */
  async initUpload(playlistId: string, metadata: { filename: string, total_size: number, total_chunks: number }) {
    try {
      const response = await apiClient.post(
        API_ROUTES.PLAYLIST_UPLOAD_INIT(playlistId),
        metadata
      )
      return response.data
    } catch (error) {
      console.error('Error initializing upload:', error)
      throw error
    }
  }

  /**
   * Uploads a single chunk of a file
   * @param playlistId - ID of the playlist
   * @param formData - FormData containing session_id, chunk_index, and file chunk
   * @returns Promise resolving to chunk upload result
   */
  async uploadChunk(playlistId: string, formData: FormData) {
    try {
      const response = await apiClient.post(
        API_ROUTES.PLAYLIST_UPLOAD_CHUNK(playlistId),
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' }
        }
      )
      return response.data
    } catch (error) {
      console.error('Error uploading chunk:', error)
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
        API_ROUTES.PLAYLIST_UPLOAD_FINALIZE(playlistId),
        data
      )
      return response.data
    } catch (error) {
      console.error('Error finalizing upload:', error)
      throw error
    }
  }

  /**
   * Gets the status of an upload session
   * @param sessionId - ID of the upload session
   * @returns Promise resolving to session status
   */
  async getUploadStatus(sessionId: string) {
    try {
      const response = await apiClient.get(
        API_ROUTES.PLAYLIST_UPLOAD_STATUS(sessionId)
      )
      return response.data
    } catch (error) {
      console.error('Error getting upload status:', error)
      throw error
    }
  }

  /**
   * Reorder tracks in a playlist
   * @param playlistId - ID of the playlist
   * @param newOrder - Array of track numbers/IDs
   * @returns Promise resolving to server response
   */
  async reorderTracks(playlistId: string, newOrder: number[]) {
    try {
      const response = await apiClient.post(API_ROUTES.PLAYLIST_REORDER(playlistId), { order: newOrder })
      return response.data
    } catch (error) {
      console.error('Error reordering tracks:', error)
      throw error
    }
  }

  /**
   * Move a track from one playlist to another
   * @param sourcePlaylistId - ID of the source playlist
   * @param targetPlaylistId - ID of the target playlist
   * @param trackNumber - Number of the track to move
   * @param targetPosition - Optional position in target playlist
   * @returns Promise resolving to server response
   */
  async moveTrackBetweenPlaylists(
    sourcePlaylistId: string,
    targetPlaylistId: string,
    trackNumber: number,
    targetPosition?: number
  ) {
    try {
      const response = await apiClient.post(API_ROUTES.MOVE_TRACK(sourcePlaylistId), {
        track_number: trackNumber,
        target_playlist_id: targetPlaylistId,
        target_position: targetPosition
      })
      return response.data
    } catch (error) {
      console.error('Error moving track between playlists:', error)
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
      console.error('Error deleting track:', error)
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
      console.error('Error deleting tracks:', error)
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
      console.debug('Start playlist response:', response.data)
      return response.data
    } catch (error) {
      console.error('Error starting playlist:', error)
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
      console.error('Error controlling playlist:', error);
      throw error;
    }
  }

  // Playback status is handled via WebSocket events (PLAYBACK_STATUS, TRACK_PROGRESS, etc.)
  // Use WebSocket listeners instead of polling an API endpoint

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
      console.error('Error downloading YouTube audio:', error)
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
      const response = await apiClient.get(API_ROUTES.HEALTH)
      return response.data
    } catch (error) {
      console.error('Error fetching health status:', error)
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
      console.error('Error getting volume:', error)
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
      console.error('Error setting volume:', error)
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
    if (cache.has(cacheKey)) {
      return cache.get(cacheKey)
    }
    try {
      console.log('Fetching audio files from API...')
      const response = await apiClient.get('/api/nfc_mapping')
      console.log('Audio files response:', response.data)

      const playlists = response.data
      console.log('Playlists transformées:', playlists)

      cache.set(cacheKey, playlists)
      return playlists
    } catch (err) {
      const error = err as AxiosError
      console.error('Error fetching audio files:', {
        response: error.response?.data,
        status: error.response?.status,
        headers: error.response?.headers
      })
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
    // If backend supports session endpoint, implement it; otherwise, mock it
    try {
      const response = await apiClient.get('/api/uploads/session_id');
      return response.data.session_id;
    } catch (error) {
      // fallback: generate a UUID if endpoint does not exist
      return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
      });
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
      onDownloadProgress: (progressEvent: any) => {
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
   * Initiates NFC association between a tag and a playlist
   * @param tagId - NFC tag identifier
   * @param playlistId - Playlist identifier
   * @returns Promise resolving to association status
   */
  async initiateNfcAssociation(tagId: string, playlistId: string) {
    try {
      const response = await apiClient.post(API_ROUTES.NFC_LINK, { tag_id: tagId, playlist_id: playlistId })
      return response.data
    } catch (error) {
      console.error('Error initiating NFC association:', error)
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
      console.error('Error getting NFC status:', error)
      throw error
    }
  }

  /**
   * Starts NFC listening mode for a specific playlist
   * @param playlistId - ID of the playlist to associate
   * @returns Promise resolving to listening status
   */
  async startNfcListening(playlistId: string) {
    try {
      const response = await apiClient.post(API_ROUTES.NFC_LISTEN(playlistId))
      return response.data
    } catch (error) {
      console.error('Error starting NFC listening:', error)
      throw error
    }
  }

  /**
   * Stops NFC listening mode
   * @returns Promise resolving to stop status
   */
  async stopNfcListening() {
    try {
      const response = await apiClient.post(API_ROUTES.NFC_STOP)
      return response.data
    } catch (error) {
      console.error('Error stopping NFC listening:', error)
      throw error
    }
  }
}

export default new RealApiService()

/**
 * Real API Service
 * Provides production-ready HTTP client for communication with the backend API.
 * Features include request/response interceptors, caching, error handling, and retry logic.
 */

import axios, { AxiosError, InternalAxiosRequestConfig, AxiosResponse, AxiosProgressEvent } from 'axios'

const apiBaseUrl = process.env.VUE_APP_API_URL;
console.log('API base URL:', apiBaseUrl);

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
      const response = await apiClient.get('/api/playlists')
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
      const response = await apiClient.get(`/api/playlists/${playlistId}`)
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
      const response = await apiClient.post('/api/playlists', playlistData)
      return response.data
    } catch (error) {
      console.error('Error creating playlist:', error)
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
      const response = await apiClient.delete(`/api/playlists/${playlistId}`)
      return response.data
    } catch (error) {
      console.error('Error deleting playlist:', error)
      throw error
    }
  }

  /**
   * Upload tracks to a playlist
   * @param playlistId - ID of the playlist
   * @param files - FileList or array of files
   * @param onUploadProgress - Optional progress callback
   * @returns Promise resolving to server response
   */
  async uploadTracks(playlistId: string, files: FileList | File[], onUploadProgress?: (progressEvent: AxiosProgressEvent) => void) {
    const formData = new FormData();
    Array.from(files).forEach((file) => formData.append('files', file));
    try {
      const response = await apiClient.post(`/api/playlists/${playlistId}/tracks/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress
      });
      return response.data;
    } catch (error) {
      console.error('Error uploading tracks:', error);
      throw error;
    }
  }

  /**
   * Reorder tracks in a playlist
   * @param playlistId - ID of the playlist
   * @param newOrder - Array of track numbers/IDs
   * @returns Promise resolving to server response
   */
  async reorderTracks(playlistId: string, newOrder: any) {
    try {
      const response = await apiClient.post(`/api/playlists/${playlistId}/tracks/reorder`, newOrder)
      return response.data
    } catch (error) {
      console.error('Error reordering tracks:', error)
      throw error
    }
  }

  /**
   * Delete a track from a playlist
   * @param playlistId - ID of the playlist
   * @param trackId - ID or number of the track
   * @returns Promise resolving to server response
   */
  async deleteTrack(playlistId: string, trackId: string | number) {
    try {
      const response = await apiClient.delete(`/api/playlists/${playlistId}/tracks/${trackId}`)
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
      const response = await apiClient.delete(`/api/playlists/${playlistId}/tracks`, { data: { track_ids: trackIds } })
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
      const response = await apiClient.post(`/api/playlists/${playlistId}/start`)
      return response.data
    } catch (error) {
      console.error('Error starting playlist:', error)
      throw error
    }
  }

  /**
   * Play a specific track in a playlist
   * @param playlistId - ID of the playlist
   * @param trackNumber - Track number to play
   * @returns Promise resolving to server response
   */
  async playTrack(playlistId: string, trackNumber: number) {
    try {
      const response = await apiClient.post(`/api/playlists/${playlistId}/play/${trackNumber}`)
      return response.data
    } catch (error) {
      console.error('Error playing track:', error)
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
      console.log(`[API] Sending control action: ${action} to /api/playlists/control/${action}`)
      // Match backend: /api/playlists/control/{action}
      const response = await apiClient.post(`/api/playlists/control/${action}`, {})
      console.log(`[API] Control response:`, response.data)
      return response.data
    } catch (error) {
      console.error(`[API] Error controlling playlist with action '${action}':`, error)
      throw error
    }
  }

  /**
   * Get current playback status from the server
   * @returns Promise resolving to playback status data
   */
  async getPlaybackStatus() {
    try {
      const response = await apiClient.get('/api/playlists/playback/status')
      return response.data
    } catch (error) {
      console.error('Error getting playback status:', error)
      throw error
    }
  }

  /**
   * Upload files to a playlist (with progress events)
   * @param playlistId - ID of the playlist
   * @param files - FileList or array of files
   * @param onUploadProgress - Optional progress callback
   * @returns Promise resolving to server response
   */
  async uploadFiles(playlistId: string, files: FileList | File[], onUploadProgress?: (progressEvent: AxiosProgressEvent) => void) {
    const formData = new FormData();
    Array.from(files).forEach((file) => formData.append('files', file));
    try {
      const response = await apiClient.post(`/api/playlists/${playlistId}/files/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress
      });
      return response.data;
    } catch (error) {
      console.error('Error uploading files:', error);
      throw error;
    }
  }

  // NFC Endpoints

  /**
   * Initiate NFC association
   * @param tagId - NFC tag ID
   * @param playlistId - Playlist ID
   * @returns Promise resolving to server response
   */
  async initiateNfcAssociation(tagId: string, playlistId: string) {
    try {
      const response = await apiClient.post('/api/nfc/initiate_nfc_association', { tag_id: tagId, playlist_id: playlistId })
      return response.data
    } catch (error) {
      console.error('Error initiating NFC association:', error)
      throw error
    }
  }

  /**
   * Complete NFC association
   * @param tagId - NFC tag ID
   * @param playlistId - Playlist ID
   * @returns Promise resolving to server response
   */
  async completeNfcAssociation(tagId: string, playlistId: string) {
    try {
      const response = await apiClient.post('/api/nfc/complete_nfc_association', { tag_id: tagId, playlist_id: playlistId })
      return response.data
    } catch (error) {
      console.error('Error completing NFC association:', error)
      throw error
    }
  }

  /**
   * Disassociate an NFC tag
   * @param tagId - NFC tag ID
   * @returns Promise resolving to server response
   */
  async disassociateNfcTag(tagId: string) {
    try {
      const response = await apiClient.post('/api/nfc/disassociate_nfc_tag', { tag_id: tagId })
      return response.data
    } catch (error) {
      console.error('Error disassociating NFC tag:', error)
      throw error
    }
  }

  /**
   * Get NFC status
   * @returns Promise resolving to NFC status JSON
   */
  async getNfcStatus() {
    try {
      const response = await apiClient.get('/api/nfc/nfc_status')
      return response.data
    } catch (error) {
      console.error('Error fetching NFC status:', error)
      throw error
    }
  }

  /**
   * Start NFC listening for a playlist
   * @param playlistId - Playlist ID
   * @returns Promise resolving to server response
   */
  async startNfcListening(playlistId: string) {
    try {
      const response = await apiClient.post(`/api/nfc/start_nfc_listening/${playlistId}`)
      return response.data
    } catch (error) {
      console.error('Error starting NFC listening:', error)
      throw error
    }
  }

  /**
   * Stop NFC listening
   * @returns Promise resolving to server response
   */
  async stopNfcListening() {
    try {
      const response = await apiClient.post('/api/nfc/stop_nfc_listening')
      return response.data
    } catch (error) {
      console.error('Error stopping NFC listening:', error)
      throw error
    }
  }

  /**
   * Simulate NFC tag detection (mock/testing)
   * @param tagId - NFC tag ID
   * @returns Promise resolving to server response
   */
  async simulateTagDetection(tagId: string) {
    try {
      const response = await apiClient.post('/api/nfc/simulate_tag_detection', { tag_id: tagId })
      return response.data
    } catch (error) {
      console.error('Error simulating tag detection:', error)
      throw error
    }
  }

  // YouTube Download

  /**
   * Download YouTube audio by URL
   * @param url - YouTube video URL
   * @returns Promise resolving to download result
   */
  async downloadYouTube(url: string) {
    try {
      const response = await apiClient.post('/api/youtube/download', { url })
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
      const response = await apiClient.get('/health')
      return response.data
    } catch (error) {
      console.error('Error fetching health status:', error)
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
   * Fetches system statistics from the server
   * @returns Promise resolving to the system statistics
   */




  /**
   * Downloads a file from the server
   * @param fileId - ID of the file to download
   * @param onProgress - Optional callback for tracking download progress
   * @returns Promise resolving to the file blob
   */


  /**
   * Generates a download URL for a file
   * @param fileId - ID of the file
   * @returns URL string for downloading the file
   */


  /**
   * Requests a new upload session ID from the server
   * Used for tracking multi-part or chunked uploads
   * @returns Promise resolving to the session ID string
   */



}

export default new RealApiService()
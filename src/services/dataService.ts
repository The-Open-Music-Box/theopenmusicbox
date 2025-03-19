/**
 * Unified Data Service
 * Provides a consistent interface for data operations by selecting between
 * mock and real implementations based on environment configuration.
 *
 * This abstraction layer allows components to use the same API regardless of
 * whether the app is running in development (with mock data) or production mode.
 */

import mockDataService from './mockData'
import realApiService from './realApiService'

interface UploadOptions {
  headers?: Record<string, string>;
  onUploadProgress?: (progress: any) => void;
}

const USE_MOCK = process.env.VUE_APP_USE_MOCK === 'true'

const dataService = {
  /**
   * Checks system health status
   * @returns Promise resolving to system health data
   */
  async checkHealth() {
    return USE_MOCK
      ? mockDataService.checkHealth()
      : realApiService.checkHealth()
  },

  /**
   * Fetches available playlists
   * @returns Promise resolving to array of playlists
   */
  getPlaylists() {
    return USE_MOCK
      ? mockDataService.getAudioFiles()
      : realApiService.getAudioFiles()
  },

  /**
   * Uploads a file to the server
   * @param file - File or FormData object to upload
   * @param options - Optional configuration including progress callback
   * @returns Promise resolving to the uploaded file data
   */
  uploadFile(file: File | FormData, options?: UploadOptions) {
    return USE_MOCK
      ? mockDataService.uploadFile(file, options)
      : realApiService.uploadFile(file, options)
  },

  /**
   * Deletes a file by ID
   * @param id - ID of the file to delete
   * @returns Promise that resolves when the delete operation completes
   */
  deleteFile(id: number) {
    return USE_MOCK
      ? mockDataService.deleteFile(id)
      : realApiService.deleteFile(id)
  },

  /**
   * Fetches system statistics
   * @returns Promise resolving to system statistics
   */
  getStats() {
    return USE_MOCK
      ? mockDataService.getStats()
      : realApiService.getStats()
  },

  /**
   * Downloads a file by ID
   * @param fileId - ID of the file to download
   * @param onProgress - Optional callback for tracking download progress
   * @returns Promise resolving to the file blob
   */
  downloadFile(fileId: number, onProgress?: (progress: number) => void) {
    return USE_MOCK
      ? mockDataService.downloadFile(fileId, onProgress)
      : realApiService.downloadFile(fileId, onProgress)
  },

  /**
   * Generates a download URL for a file
   * @param fileId - ID of the file
   * @returns URL string for downloading the file
   */
  downloadFileUrl(fileId: number) {
    return USE_MOCK
      ? mockDataService.downloadFileUrl(fileId)
      : realApiService.downloadFileUrl(fileId)
  },

  /**
   * Requests a new upload session ID
   * Used for tracking multi-part or chunked uploads
   * @returns Promise resolving to the session ID string
   */
  getUploadSessionId() {
    return USE_MOCK
      ? mockDataService.getUploadSessionId()
      : realApiService.getUploadSessionId()
  }
}

export default dataService
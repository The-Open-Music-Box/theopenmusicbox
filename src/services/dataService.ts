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

const USE_MOCK = process.env.VUE_APP_USE_MOCK === 'true'

const dataService = {
  /**
   * Fetches the list of audio files from the server
   * @returns Promise resolving to the list of audio files
   */
  getAudioFiles() {
    return USE_MOCK
      ? mockDataService.getAudioFiles()
      : realApiService.getAudioFiles()
  },

  /**
   * Uploads files to a playlist (with progress events)
   * @param playlistId - ID of the playlist
   * @param files - FileList or array of files
   * @param onUploadProgress - Optional progress callback
   * @returns Promise resolving to server response
   */
  uploadFiles(playlistId: string, files: FileList | File[], onUploadProgress?: (progressEvent: any) => void) {
    return USE_MOCK
      ? mockDataService.uploadFile(files[0], { onUploadProgress }, playlistId)
      : realApiService.uploadFiles(playlistId, files, onUploadProgress)
  },

  /**
   * Generates a new upload session ID
   * @returns Promise resolving to session ID string
   */
  getUploadSessionId() {
    return USE_MOCK
      ? mockDataService.getUploadSessionId()
      : realApiService.getUploadSessionId()
  },

  /**
   * Downloads a file from the server
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
   * Download YouTube audio by URL (if supported)
   * @param url - YouTube URL
   * @returns Promise resolving to server response
   */
  downloadYouTube(url: string) {
    return USE_MOCK
      ? mockDataService.downloadYouTube(url)
      : realApiService.downloadYouTube(url)
  },
  /**
   * Checks system health status
   * @returns Promise resolving to system health data
   */
  checkHealth() {
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
      ? mockDataService.getPlaylists()
      : realApiService.getPlaylists()
  },

  /**
   * Deletes a track from a playlist
   * @param playlistId - Playlist identifier
   * @param trackId - Track identifier or number
   * @returns Promise that resolves when the delete operation completes
   */
  deleteTrack(playlistId: string, trackId: string | number) {
    return USE_MOCK
      ? mockDataService.deleteTrack(playlistId, trackId)
      : realApiService.deleteTrack(playlistId, trackId)
  },

  /**
   * Creates a new playlist
   * @param playlistData - Data for the new playlist
   * @returns Promise that resolves when the create operation completes
   */
  createPlaylist(playlistData: any) {
    return USE_MOCK
      ? mockDataService.createPlaylist(playlistData)
      : realApiService.createPlaylist(playlistData)
  },

  /**
   * Reorders tracks in a playlist
   * @param playlistId - Playlist identifier
   * @param newOrder - New order of tracks
   * @returns Promise that resolves when the reorder operation completes
   */
  reorderTracks(playlistId: string, newOrder: string[]) {
    return USE_MOCK
      ? mockDataService.reorderTracks(playlistId, newOrder)
      : realApiService.reorderTracks(playlistId, newOrder)
  },

  /**
   * Controls a playlist
   * @param action - Action to perform on the playlist
   * @returns Promise that resolves when the control operation completes
   */
  controlPlaylist(action: string) {
    return USE_MOCK
      ? mockDataService.controlPlaylist(action)
      : realApiService.controlPlaylist(action)
  },

  /**
   * Initiates NFC association
   * @param tagId - NFC tag identifier
   * @param playlistId - Playlist identifier
   * @returns Promise that resolves when the association operation completes
   */
  initiateNfcAssociation(tagId: string, playlistId: string) {
    return USE_MOCK
      ? mockDataService.initiateNfcAssociation(tagId, playlistId)
      : realApiService.initiateNfcAssociation(tagId, playlistId)
  },

  /**
   * Retrieves NFC status
   * @returns Promise resolving to NFC status data
   */
  getNfcStatus() {
    return USE_MOCK
      ? mockDataService.getNfcStatus()
      : realApiService.getNfcStatus()
  }
}

export default dataService
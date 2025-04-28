/**
 * Unified Data Service
 * Provides a consistent interface for data operations.
 *
 * This abstraction layer allows components to use the same API regardless of
 * the environment.
 */

import realApiService from './realApiService'

const dataService = {
  /**
   * Fetches the list of audio files from the server
   * @returns Promise resolving to the list of audio files
   */
  getAudioFiles() {
    return realApiService.getAudioFiles();
  },

  /**
   * Uploads files to a playlist (with progress events)
   * @param playlistId - ID of the playlist
   * @param files - FileList or array of files
   * @param onUploadProgress - Optional progress callback
   * @returns Promise resolving to server response
   */
  uploadFiles(playlistId: string, files: FileList | File[], onUploadProgress?: (progressEvent: any) => void) {
    return realApiService.uploadFiles(playlistId, files, onUploadProgress);
  },

  /**
   * Generates a new upload session ID
   * @returns Promise resolving to session ID string
   */
  getUploadSessionId() {
    return realApiService.getUploadSessionId();
  },

  /**
   * Downloads a file from the server
   * @param fileId - ID of the file to download
   * @param onProgress - Optional callback for tracking download progress
   * @returns Promise resolving to the file blob
   */
  downloadFile(fileId: number, onProgress?: (progress: number) => void) {
    return realApiService.downloadFile(fileId, onProgress);
  },

  /**
   * Generates a download URL for a file
   * @param fileId - ID of the file
   * @returns URL string for downloading the file
   */
  downloadFileUrl(fileId: number) {
    return realApiService.downloadFileUrl(fileId);
  },

  /**
   * Download YouTube audio by URL (if supported)
   * @param url - YouTube URL
   * @returns Promise resolving to server response
   */
  downloadYouTube(url: string) {
    return realApiService.downloadYouTube(url);
  },

  /**
   * Checks system health status
   * @returns Promise resolving to system health data
   */
  checkHealth() {
    return realApiService.checkHealth();
  },

  /**
   * Fetches available playlists
   * @returns Promise resolving to array of playlists
   */
  getPlaylists() {
    return realApiService.getPlaylists();
  },

  /**
   * Deletes a track from a playlist
   * @param playlistId - Playlist identifier
   * @param trackId - Track identifier or number
   * @returns Promise that resolves when the delete operation completes
   */
  deleteTrack(playlistId: string, trackId: string | number) {
    return realApiService.deleteTrack(playlistId, trackId);
  },

  /**
   * Creates a new playlist
   * @param playlistData - Data for the new playlist
   * @returns Promise that resolves when the create operation completes
   */
  createPlaylist(playlistData: any) {
    return realApiService.createPlaylist(playlistData);
  },

  /**
   * Reorders tracks in a playlist
   * @param playlistId - Playlist identifier
   * @param newOrder - New order of tracks
   * @returns Promise that resolves when the reorder operation completes
   */
  reorderTracks(playlistId: string, newOrder: string[]) {
    return realApiService.reorderTracks(playlistId, newOrder);
  },

  /**
   * Controls a playlist
   * @param action - Action to perform on the playlist
   * @returns Promise that resolves when the control operation completes
   */
  controlPlaylist(action: string) {
    return realApiService.controlPlaylist(action);
  },

  /**
   * Initiates NFC association
   * @param tagId - NFC tag identifier
   * @param playlistId - Playlist identifier
   * @returns Promise that resolves when the association operation completes
   */
  initiateNfcAssociation(tagId: string, playlistId: string) {
    return realApiService.initiateNfcAssociation(tagId, playlistId);
  },

  /**
   * Retrieves NFC status
   * @returns Promise resolving to NFC status data
   */
  getNfcStatus() {
    return realApiService.getNfcStatus();
  }
}

export default dataService
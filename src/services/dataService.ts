/**
 * Unified Data Service
 * Provides a consistent interface for data operations.
 *
 * This abstraction layer allows components to use the same API regardless of
 * the environment.
 */

import realApiService from './realApiService'
import { AxiosProgressEvent } from 'axios'
import cacheService from './cacheService'

const dataService = {
  /**
   * Start playback of a playlist
   * @param playlistId - Playlist identifier
   * @returns Promise resolving to server response
   */
  startPlaylist(playlistId: string) {
    return realApiService.startPlaylist(playlistId);
  },
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
   * @deprecated Use initUpload, uploadChunk, and finalizeUpload instead
   */
  uploadFiles(playlistId: string, files: FileList | File[], onUploadProgress?: (progressEvent: AxiosProgressEvent) => void) {
    return realApiService.uploadFiles(playlistId, files, onUploadProgress);
  },

  /**
   * Initializes a chunked upload session
   * @param playlistId - ID of the playlist
   * @param metadata - File metadata (filename, file_size)
   * @returns Promise resolving to session initialization data
   */
  initUpload(playlistId: string, metadata: { filename: string, file_size: number }) {
    return realApiService.initUpload(playlistId, metadata);
  },

  /**
   * Uploads a single chunk of a file
   * @param playlistId - ID of the playlist
   * @param sessionId - ID of the upload session
   * @param chunkIndex - Index of the chunk being uploaded
   * @param formData - FormData containing the file chunk
   * @returns Promise resolving to chunk upload result
   */
  uploadChunk(playlistId: string, sessionId: string, chunkIndex: number, formData: FormData) {
    return realApiService.uploadChunk(playlistId, sessionId, chunkIndex, formData);
  },

  /**
   * Finalizes a chunked upload session
   * @param playlistId - ID of the playlist
   * @param data - Session data for finalization
   * @returns Promise resolving to finalization result
   */
  finalizeUpload(playlistId: string, data: { session_id: string }) {
    return realApiService.finalizeUpload(playlistId, data);
  },

  /**
   * Gets the status of an upload session
   * @param playlistId - ID of the playlist
   * @param sessionId - ID of the upload session
   * @returns Promise resolving to session status
   */
  getUploadStatus(playlistId: string, sessionId: string) {
    return realApiService.getUploadStatus(playlistId, sessionId);
  },

  /**
   * Generates a new upload session ID
   * @returns Promise resolving to session ID string
   * @deprecated No longer needed with chunked upload
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
  async getPlaylists() {
    const cacheKey = 'all-playlists';
    const cachedData = cacheService.get(cacheKey);
    
    if (cachedData) {
      return cachedData;
    }
    
    const data = await realApiService.getPlaylists();
    cacheService.set(cacheKey, data);
    
    return data;
  },

  /**
   * Gets a specific playlist from the server with caching
   * @param playlistId - Playlist identifier
   * @returns Promise resolving to the requested playlist
   */
  async getPlaylist(playlistId: string) {
    const cachedData = cacheService.get(playlistId);
    
    if (cachedData) {
      return cachedData;
    }
    
    const data = await realApiService.getPlaylist(playlistId);
    cacheService.set(playlistId, data);
    
    return data;
  },

  /**
   * Deletes a track from a playlist
   * @param playlistId - Playlist identifier
   * @param trackNumber - Track number
   * @returns Promise that resolves when the delete operation completes
   */
  deleteTrack(playlistId: string, trackNumber: number) {
    return realApiService.deleteTrack(playlistId, trackNumber);
  },

  /**
   * Creates a new playlist
   * @param playlistData - Data for the new playlist
   * @returns Promise that resolves when the create operation completes
   */
  createPlaylist(playlistData: { title: string }) {
    return realApiService.createPlaylist(playlistData);
  },

  /**
   * Updates a playlist
   * @param playlistId - Playlist identifier
   * @param playlistData - Data to update the playlist
   * @returns Promise that resolves when the update operation completes
   */
  updatePlaylist(playlistId: string, playlistData: { title?: string; [key: string]: unknown }) {
    return realApiService.updatePlaylist(playlistId, playlistData);
  },

  /**
   * Reorders tracks in a playlist
   * @param playlistId - Playlist identifier
   * @param trackOrder - New order of tracks (as numbers)
   * @returns Promise that resolves when the reorder operation completes
   */
  reorderTracks(playlistId: string, trackOrder: number[]) {
    return realApiService.reorderTracks(playlistId, trackOrder);
  },

  /**
   * Play a specific track in a playlist
   * @param playlistId - Playlist identifier
   * @param trackNumber - Track number to play
   * @returns Promise that resolves when the play operation completes
   */
  playTrack(playlistId: string, trackNumber: number) {
    return realApiService.playTrack(playlistId, trackNumber);
  },

  /**
   * Get current playback status
   * @returns Promise resolving to playback status
   */
  getPlaybackStatus() {
    return realApiService.getPlaybackStatus();
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
   * Associate an NFC tag with a playlist
   * @param nfcTagId - NFC tag identifier
   * @param playlistId - Playlist identifier
   * @returns Promise that resolves when the association operation completes
   */
  associateNfcTag(nfcTagId: string, playlistId: string) {
    return realApiService.associateNfcTag(nfcTagId, playlistId);
  },

  /**
   * Remove NFC association from a playlist
   * @param playlistId - Playlist identifier
   * @returns Promise that resolves when the removal operation completes
   */
  removeNfcAssociation(playlistId: string) {
    return realApiService.removeNfcAssociation(playlistId);
  },

  /**
   * Get playlist associated with an NFC tag
   * @param nfcTagId - NFC tag identifier
   * @returns Promise resolving to associated playlist
   */
  getNfcPlaylist(nfcTagId: string) {
    return realApiService.getNfcPlaylist(nfcTagId);
  },

  /**
   * Scan for available NFC tags
   * @returns Promise resolving to scan results
   */
  scanNfcTags() {
    return realApiService.scanNfcTags();
  },

  /**
   * Write data to an NFC tag
   * @param tagId - NFC tag identifier
   * @param data - Data to write to the tag
   * @returns Promise resolving to write status
   */
  writeNfcTag(tagId: string, data: string) {
    return realApiService.writeNfcTag(tagId, data);
  },

  /**
   * Retrieves NFC status
   * @returns Promise resolving to NFC status data
   */
  getNfcStatus() {
    return realApiService.getNfcStatus();
  },

  /**
   * Invalidates the cache for a specific playlist or all playlists
   * @param playlistId - Playlist identifier, or undefined to clear all
   */
  invalidatePlaylistCache(playlistId?: string) {
    cacheService.invalidatePlaylistCache(playlistId);
  },
  
  /**
   * Invalidates the files cache
   */
  invalidateFilesCache() {
    cacheService.invalidateFilesCache();
  },

  /**
   * Search YouTube videos
   * @param query - Search query
   * @param maxResults - Maximum number of results (optional)
   * @returns Promise resolving to search results
   */
  searchYouTube(query: string, maxResults?: number) {
    return realApiService.searchYouTube(query, maxResults);
  },

  /**
   * Get YouTube download task status
   * @param taskId - Task identifier
   * @returns Promise resolving to task status
   */
  getYouTubeStatus(taskId: string) {
    return realApiService.getYouTubeStatus(taskId);
  },

  /**
   * Get system information
   * @returns Promise resolving to system info
   */
  getSystemInfo() {
    return realApiService.getSystemInfo();
  },

  /**
   * Get system logs
   * @returns Promise resolving to system logs
   */
  getSystemLogs() {
    return realApiService.getSystemLogs();
  },

  /**
   * Restart the system
   * @returns Promise resolving to restart status
   */
  restartSystem() {
    return realApiService.restartSystem();
  },

  /**
   * Sync playlists with filesystem
   * @returns Promise resolving to sync status
   */
  syncPlaylists() {
    return realApiService.syncPlaylists();
  },

  /**
   * Move a track from one playlist to another
   * @param sourcePlaylistId - Source playlist identifier
   * @param targetPlaylistId - Target playlist identifier
   * @param trackNumber - Track number to move
   * @param targetPosition - Position in target playlist (optional)
   * @returns Promise resolving to move operation result
   */
  moveTrackBetweenPlaylists(
    sourcePlaylistId: string,
    targetPlaylistId: string,
    trackNumber: number,
    targetPosition?: number
  ) {
    return realApiService.moveTrackBetweenPlaylists(
      sourcePlaylistId,
      targetPlaylistId,
      trackNumber,
      targetPosition
    );
  }
}

export default dataService
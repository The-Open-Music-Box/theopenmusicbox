/**
 * Unified Data Service
 * Provides a consistent interface for data operations.
 *
 * This abstraction layer allows components to use the same API regardless of
 * the environment.
 */

import realApiService from './realApiService'

// Cache pour les playlists avec TTL
const playlistCache = new Map<string, { data: any; timestamp: number }>();
const filesCache = new Map<string, { data: any; timestamp: number }>();
const CACHE_TTL = 30000; // 30 secondes

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
  uploadFiles(playlistId: string, files: FileList | File[], onUploadProgress?: (progressEvent: any) => void) {
    return realApiService.uploadFiles(playlistId, files, onUploadProgress);
  },

  /**
   * Initializes a chunked upload session
   * @param playlistId - ID of the playlist
   * @param metadata - File metadata (filename, size, chunks)
   * @returns Promise resolving to session initialization data
   */
  initUpload(playlistId: string, metadata: { filename: string, total_size: number, total_chunks: number }) {
    return realApiService.initUpload(playlistId, metadata);
  },

  /**
   * Uploads a single chunk of a file
   * @param playlistId - ID of the playlist
   * @param formData - FormData containing session_id, chunk_index, and file chunk
   * @returns Promise resolving to chunk upload result
   */
  uploadChunk(playlistId: string, formData: FormData) {
    return realApiService.uploadChunk(playlistId, formData);
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
   * @param sessionId - ID of the upload session
   * @returns Promise resolving to session status
   */
  getUploadStatus(sessionId: string) {
    return realApiService.getUploadStatus(sessionId);
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
    const now = Date.now();
    const cacheKey = 'all-playlists';
    const cacheEntry = playlistCache.get(cacheKey);
    
    if (cacheEntry && now - cacheEntry.timestamp < CACHE_TTL) {
      return cacheEntry.data;
    }
    
    const data = await realApiService.getPlaylists();
    playlistCache.set(cacheKey, {
      data,
      timestamp: now
    });
    
    return data;
  },

  /**
   * Gets a specific playlist from the server with caching
   * @param playlistId - Playlist identifier
   * @returns Promise resolving to the requested playlist
   */
  async getPlaylist(playlistId: string) {
    const now = Date.now();
    const cacheEntry = playlistCache.get(playlistId);
    
    if (cacheEntry && now - cacheEntry.timestamp < CACHE_TTL) {
      return cacheEntry.data;
    }
    
    const data = await realApiService.getPlaylist(playlistId);
    playlistCache.set(playlistId, {
      data,
      timestamp: now
    });
    
    return data;
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
   * Updates a playlist
   * @param playlistId - Playlist identifier
   * @param playlistData - Data to update the playlist
   * @returns Promise that resolves when the update operation completes
   */
  updatePlaylist(playlistId: string, playlistData: any) {
    return realApiService.updatePlaylist(playlistId, playlistData);
  },

  /**
   * Reorders tracks in a playlist
   * @param playlistId - Playlist identifier
   * @param newOrder - New order of tracks (as numbers)
   * @returns Promise that resolves when the reorder operation completes
   */
  reorderTracks(playlistId: string, newOrder: number[]) {
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
  },

  /**
   * Invalidates the cache for a specific playlist or all playlists
   * @param playlistId - Playlist identifier, or undefined to clear all
   */
  invalidatePlaylistCache(playlistId?: string) {
    if (playlistId) {
      playlistCache.delete(playlistId);
    } else {
      playlistCache.clear();
    }
  },
  
  /**
   * Invalidates the files cache
   */
  invalidateFilesCache() {
    filesCache.clear();
  }
}

export default dataService
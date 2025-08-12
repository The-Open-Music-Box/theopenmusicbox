/**
 * Upload Store
 * 
 * Centralized store for managing chunked uploads
 * Provides a reactive state and methods to track and update uploads.
 */

import { reactive } from 'vue';
import dataService from '../services/dataService';
import { eventBus } from '../services/eventBus';

interface FileInfo {
  filename: string;
  size: number;
  type: string;
}

interface UploadInfo {
  fileInfo: FileInfo;
  playlistId: string;
  progress: number;
  startTime?: number;
}

interface CompletedUpload extends UploadInfo {
  fileData: {
    fileId?: string;
    fileName: string;
  };
  completedAt: number;
}

interface UploadState {
  uploads: Map<string, UploadInfo>;
  completedUploads: CompletedUpload[];
}

export interface UploadStore {
  state: UploadState;
  registerUpload(sessionId: string, fileInfo: FileInfo, playlistId: string): void;
  updateProgress(sessionId: string, progress: number): void;
  completeUpload(sessionId: string, fileData: { fileId?: string; fileName: string }): void;
  failUpload(sessionId: string, error: any): void;
  refreshPlaylist(playlistId: string): Promise<any>;
  invalidateCache(playlistId?: string): void;
}

export const uploadStore: UploadStore = {
  // Reactive state
  state: reactive<UploadState>({
    uploads: new Map<string, UploadInfo>(),
    completedUploads: [],
  }),
  
  /**
   * Register a new upload
   * @param sessionId - Upload session ID
   * @param fileInfo - File information
   * @param playlistId - Playlist ID
   */
  registerUpload(sessionId: string, fileInfo: FileInfo, playlistId: string) {
    this.state.uploads.set(sessionId, { 
      fileInfo, 
      playlistId, 
      progress: 0, 
      startTime: Date.now() 
    });
    
    // Notify upload start
    eventBus.emit('upload-started', sessionId, playlistId, fileInfo);
  },
  
  /**
   * Update the progress of an upload
   * @param sessionId - Upload session ID
   * @param progress - Progress (0-100)
   */
  updateProgress(sessionId: string, progress: number) {
    const upload = this.state.uploads.get(sessionId);
    if (upload) {
      upload.progress = progress;
      
      // Notify progress
      eventBus.emit('upload-progress', sessionId, progress, upload);
    }
  },
  
  /**
   * Mark an upload as completed
   * @param sessionId - Upload session ID
   * @param fileData - Uploaded file data
   */
  completeUpload(sessionId: string, fileData: { fileId?: string; fileName: string }) {
    const upload = this.state.uploads.get(sessionId);
    if (upload) {
      const completedUpload: CompletedUpload = {
        ...upload,
        fileData,
        completedAt: Date.now()
      };
      this.state.completedUploads.push(completedUpload);
      this.state.uploads.delete(sessionId);
      // Periodically clean up the completed uploads list
      if (this.state.completedUploads.length > 10) {
        this.state.completedUploads.shift(); // Keep only the last 10
      }
      // Notify upload completion and trigger refresh
      eventBus.emit('upload-completed', sessionId, upload.playlistId, fileData);
      void this.refreshPlaylist(upload.playlistId);
    }
  },
  
  /**
   * Handle an upload error
   * @param sessionId - Upload session ID
   * @param error - Encountered error
   */
  failUpload(sessionId: string, error: any) {
    const upload = this.state.uploads.get(sessionId);
    if (upload) {
      this.state.uploads.delete(sessionId);
      
      // Notify error
      eventBus.emit('upload-error', sessionId, upload.playlistId, error);
    }
  },
  
  /**
   * Refreshes a playlist's data after an upload
   * @param playlistId - ID of the playlist to refresh
   */
  async refreshPlaylist(playlistId: string): Promise<any> {
    try {
      // Invalidate cache for this playlist
      dataService.invalidatePlaylistCache(playlistId);
      
      // Fetch updated data
      const updatedPlaylist = await dataService.getPlaylist(playlistId);
      
      // Notify subscribed components
      eventBus.emit('playlist-updated', playlistId, updatedPlaylist);
      
      return updatedPlaylist;
    } catch (error) {
      console.error('Error refreshing playlist:', error);
      eventBus.emit('playlist-refresh-error', playlistId, error);
      return null;
    }
  },
  
  /**
   * Invalidate the cache for a playlist
   * @param playlistId - Playlist ID (or null to invalidate all)
   */
  invalidateCache(playlistId?: string) {
    dataService.invalidatePlaylistCache(playlistId);
  }
};

// Export as singleton
export default uploadStore;

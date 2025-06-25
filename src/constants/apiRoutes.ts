/**
 * API Routes Constants
 * 
 * This file centralizes all API routes and socket events used in the application.
 * All routes are aligned with the backend API documentation found in /back/routes-api.md
 */

/**
 * Base API routes
 */
export const API_ROUTES = {
  // Playlists
  PLAYLISTS: '/api/playlists',
  PLAYLIST: (id: string) => `/api/playlists/${id}`,
  PLAYLIST_UPLOAD: (id: string) => `/api/playlists/${id}/upload`,
  PLAYLIST_REORDER: (id: string) => `/api/playlists/${id}/reorder`,
  PLAYLIST_TRACK: (playlistId: string, trackId: string | number) => 
    `/api/playlists/${playlistId}/tracks/${trackId}`,
  
  // Playback
  PLAYBACK_START: (id: string) => `/api/playlists/${id}/start`,
  PLAYBACK_TRACK: (playlistId: string, trackNumber: number) => 
    `/api/playlists/${playlistId}/play/${trackNumber}`,
  PLAYBACK_CONTROL: '/api/playlists/control',
  // Note: PLAYBACK_STATUS route not found in backend documentation, may be replaced by WebSocket events
  PLAYBACK_STATUS: '/api/playback/status', // TODO: Verify if this route exists or should be removed
  
  // NFC
  NFC_OBSERVE: '/api/nfc/observe',
  NFC_LINK: '/api/nfc/link',
  NFC_CANCEL: '/api/nfc/cancel',
  NFC_STATUS: '/api/nfc/status',
  NFC_LISTEN: (playlistId: string) => `/api/nfc/listen/${playlistId}`,
  NFC_STOP: '/api/nfc/stop',
  NFC_SIMULATE_TAG: '/api/nfc/simulate_tag',
  
  // YouTube
  YOUTUBE_DOWNLOAD: '/api/youtube/download',
  
  // System
  HEALTH: '/api/health',
  VOLUME: '/api/volume',
}

/**
 * Socket events
 */
export const SOCKET_EVENTS = {
  // Connection events
  CONNECT: 'connect',
  DISCONNECT: 'disconnect',
  CONNECT_ERROR: 'connect_error',
  RECONNECT: 'reconnect',
  ERROR: 'error',
  CONNECTION_STATUS: 'connection_status',
  
  // Playback events - Received from server
  PLAYBACK_STATUS: 'playback_status',
  PLAYBACK_STARTED: 'playback_started',
  PLAYBACK_STOPPED: 'playback_stopped',
  PLAYBACK_PAUSED: 'playback_paused',
  PLAYBACK_RESUMED: 'playback_resumed',
  TRACK_CHANGED: 'track_changed',
  TRACK_PROGRESS: 'track_progress',
  PLAYBACK_PROGRESS: 'playback_progress', // Alias for TRACK_PROGRESS for backward compatibility
  PLAYBACK_ERROR: 'playback_error',
  TRACK_PLAYED: 'track_played',
  
  // Playback events - Sent to server
  SET_PLAYLIST: 'set_playlist',
  PLAY_TRACK: 'play_track',
  PLAYLIST_SET: 'playlist_set',
  
  // NFC events - Received from server
  NFC_TAG_DETECTED: 'nfc_tag_detected',
  NFC_ASSOCIATION_COMPLETE: 'nfc_association_complete',
  NFC_ERROR: 'nfc_error',
  NFC_STATUS: 'nfc_status',
  
  // NFC events - Sent to server
  START_NFC_LINK: 'start_nfc_link',
  STOP_NFC_LINK: 'stop_nfc_link',
  OVERRIDE_NFC_TAG: 'override_nfc_tag',
  
  // Upload events
  UPLOAD_PROGRESS: 'upload_progress',
  UPLOAD_COMPLETE: 'upload_complete',
  UPLOAD_ERROR: 'upload_error',
  
  // System events
  VOLUME_CHANGED: 'volume_changed',
  SYSTEM_HEALTH: 'system_health',
}

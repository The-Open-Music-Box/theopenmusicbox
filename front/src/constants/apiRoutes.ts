/**
 * API Routes Constants
 *
 * This file centralizes all API routes and socket events used in the application.
 * All routes are aligned with the backend API documentation found in /documentation/routes-api.md
 */

/**
 * Base API routes
 */
export const API_ROUTES = {
  // Playlists
  PLAYLISTS: '/api/playlists/',
  PLAYLIST: (id: string) => `/api/playlists/${id}`,
  PLAYLIST_UPLOAD: (id: string) => `/api/playlists/${id}/upload`,
  // Chunked upload routes (REST compliant)
  PLAYLIST_UPLOAD_SESSION: (id: string) => `/api/playlists/${id}/uploads/session`,
  PLAYLIST_UPLOAD_CHUNK: (playlistId: string, sessionId: string, chunkIndex: number) => 
    `/api/playlists/${playlistId}/uploads/${sessionId}/chunks/${chunkIndex}`,
  PLAYLIST_UPLOAD_FINALIZE: (playlistId: string, sessionId: string) => 
    `/api/playlists/${playlistId}/uploads/${sessionId}/finalize`,
  PLAYLIST_UPLOAD_STATUS: (playlistId: string, sessionId: string) => 
    `/api/playlists/${playlistId}/uploads/${sessionId}`,
  PLAYLIST_REORDER: (id: string) => `/api/playlists/${id}/reorder`,
  DELETE_TRACKS: (id: string) => `/api/playlists/${id}/tracks`,
  PLAYLIST_TRACK: (playlistId: string, trackNumber: number) =>
    `/api/playlists/${playlistId}/play/${trackNumber}`,
  PLAYLIST_SYNC: '/api/playlists/sync',

  // Playback
  PLAYBACK_START: (id: string) => `/api/playlists/${id}/start`,
  PLAYBACK_TRACK: (playlistId: string, trackNumber: number) =>
    `/api/playlists/${playlistId}/play/${trackNumber}`,
  PLAYBACK_CONTROL: '/api/playlists/control',
  PLAYBACK_STATUS: '/api/playback/status',

  // NFC
  NFC_STATUS: '/api/nfc/status',
  NFC_SCAN: '/api/nfc/scan',
  NFC_WRITE: '/api/nfc/write',
  NFC_ASSOCIATE: (nfcTagId: string, playlistId: string) => `/api/playlists/nfc/${nfcTagId}/associate/${playlistId}`,
  NFC_REMOVE_ASSOCIATION: (playlistId: string) => `/api/playlists/nfc/${playlistId}`,
  NFC_GET_PLAYLIST: (nfcTagId: string) => `/api/playlists/nfc/${nfcTagId}`,

  // YouTube
  YOUTUBE_SEARCH: '/api/youtube/search',
  YOUTUBE_DOWNLOAD: '/api/youtube/download',
  YOUTUBE_STATUS: (taskId: string) => `/api/youtube/status/${taskId}`,

  // System
  SYSTEM_INFO: '/api/system/info',
  SYSTEM_LOGS: '/api/system/logs',
  SYSTEM_RESTART: '/api/system/restart',
  VOLUME: '/api/volume',

  // Upload management utilities
  UPLOAD_SESSIONS_LIST: '/api/uploads/sessions',
  UPLOAD_SESSION_DELETE: (sessionId: string) => `/api/uploads/sessions/${sessionId}`,
  UPLOAD_CLEANUP: '/api/uploads/cleanup',
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

  // Upload events (enhanced)
  UPLOAD_SESSION_CREATED: 'upload_session_created',
  UPLOAD_PROGRESS: 'upload_progress',
  UPLOAD_COMPLETE: 'upload_complete',
  UPLOAD_ERROR: 'upload_error',
  UPLOAD_SESSION_EXPIRED: 'upload_session_expired',
  
  // Playback state events
  PLAYBACK_STATE_CHANGED: 'playback_state_changed',

  // System events
  VOLUME_CHANGED: 'volume_changed',
  SYSTEM_HEALTH: 'system_health',
}

/**
 * Types for the audio file management system
 */

/**
 * File status options that define the current state of a file
 */
export type FileStatus = 'pending' | 'processing' | 'ready' | 'error';

/**
 * Enum-like object for backward compatibility
 */
export const FILE_STATUS = {
  PENDING: 'pending' as FileStatus,
  IN_PROGRESS: 'processing' as FileStatus,
  READY: 'ready' as FileStatus,
  ERROR: 'error' as FileStatus,
  ASSOCIATED: 'ready' as FileStatus, // Adding missing constant
};

/**
 * CSS classes for different file statuses
 */
export const STATUS_CLASSES: Record<FileStatus, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  processing: 'bg-blue-100 text-blue-800',
  ready: 'bg-green-100 text-green-800',
  error: 'bg-red-100 text-red-800',
};

/**
 * Basic content interface that all content types extend
 */
export interface BaseContent {
  id: string;
  type: string;
}

/**
 * Represents a track in a playlist
 */
export interface Track {
  number: number;
  title: string;
  filename: string;
  duration: string;
  play_counter: number;
}

/**
 * Represents a playlist containing multiple tracks
 */
export interface PlayList extends BaseContent {
  type: 'playlist';
  title: string;
  description?: string;
  last_played: number; // Unix timestamp in milliseconds
  tracks: Track[];
  created_at?: string;
}

/**
 * Legacy playlist format for backward compatibility
 */
export interface LegacyPlayList {
  id: string;
  title: string;
  description?: string;
  tracks: Track[];
  lastPlayed?: Date;
}

/**
 * Basic audio file properties
 */
export interface AudioFile {
  id: string;
  name: string;
  status: FileStatus;
  size: number;
  type: string;
}

/**
 * Legacy audio file format for backward compatibility
 */
export interface LegacyAudioFile extends AudioFile {
  path: string;
  uploaded: string;
  metadata?: Record<string, unknown>; // Using unknown instead of any
}

/**
 * Hook interface for event handling
 */
export interface Hook extends BaseContent {
  type: 'hook';
  idtagnfc: string;
  path: string;
  created_at: string;
}

/**
 * Convert a modern playlist to legacy format
 * @param playlist - Modern playlist format
 * @returns Legacy playlist format
 */
export function playlistToLegacy(playlist: PlayList): LegacyPlayList {
  return {
    id: playlist.id,
    title: playlist.title,
    description: playlist.description,
    tracks: playlist.tracks,
    lastPlayed: playlist.last_played ? new Date(playlist.last_played * 1000) : undefined
  };
}
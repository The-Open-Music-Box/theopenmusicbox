// components/files/types.ts

// Define the possible status values as a union type
export const FILE_STATUS = {
  ASSOCIATED: 'associer',
  IN_PROGRESS: 'In progress',
  ARCHIVED: 'Archived',
} as const

// Create a type from the object values
export type FileStatus = typeof FILE_STATUS[keyof typeof FILE_STATUS]

// Define the possible content types
export type ContentType = 'playlist' | 'hook'

// Base interface for both playlist and hook types
export interface BaseContent {
  id: string
  type: ContentType
  idtagnfc: string
  path: string
  created_at: string
}

// Track interface matching backend structure
export interface Track {
  number: number
  title: string
  filename: string
  duration: string
  play_counter: number
}

// Playlist interface matching backend structure
export interface PlayList extends BaseContent {
  type: 'playlist'
  title: string
  tracks: Track[]
  last_played: string
}

// Hook interface matching backend structure
export interface Hook extends BaseContent {
  type: 'hook'
}

// Legacy interfaces for backward compatibility
export interface LegacyAudioFile {
  id: number
  name: string
  status: FileStatus
  duration: number
  createdAt: string
  playlistId?: number
  isAlbum?: boolean
  albumFiles?: LegacyAudioFile[]
}

export interface LegacyPlayList {
  id: number
  name: string
  files: LegacyAudioFile[]
}

// Type-safe status styling configuration
export const STATUS_CLASSES: Record<FileStatus, string> = {
  [FILE_STATUS.ASSOCIATED]: 'text-green-700 bg-green-50 ring-green-600/20',
  [FILE_STATUS.IN_PROGRESS]: 'text-gray-600 bg-gray-50 ring-gray-500/10',
  [FILE_STATUS.ARCHIVED]: 'text-yellow-800 bg-yellow-50 ring-yellow-600/20'
}

// Helper function to validate status
export function isValidFileStatus(status: string): status is FileStatus {
  return Object.values(FILE_STATUS).includes(status as FileStatus)
}

// Helper function to convert Track to LegacyAudioFile
export function trackToLegacyAudioFile(track: Track, playlistId?: number): LegacyAudioFile {
  return {
    id: track.number,
    name: track.filename,
    status: FILE_STATUS.IN_PROGRESS,
    duration: parseInt(track.duration) || 0,
    createdAt: new Date().toISOString(),
    playlistId,
    isAlbum: false
  }
}

// Helper function to convert PlayList to LegacyPlayList
export function playlistToLegacy(playlist: PlayList): LegacyPlayList {
  return {
    id: parseInt(playlist.id) || Math.floor(Math.random() * 1000),
    name: playlist.title,
    files: playlist.tracks.map(track => trackToLegacyAudioFile(track, parseInt(playlist.id)))
  }
}
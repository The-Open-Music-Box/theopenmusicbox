// components/files/types.ts

// Define the possible status values as a union type
export const FILE_STATUS = {
  ASSOCIATED: 'associer',
  IN_PROGRESS: 'In progress',
  ARCHIVED: 'Archived',
} as const

// Create a type from the object values
export type FileStatus = typeof FILE_STATUS[keyof typeof FILE_STATUS]

// Update the AudioFile interface to use the new FileStatus type
export interface AudioFile {
  id: number
  name: string
  status: FileStatus
  duration: number
  createdAt: string
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
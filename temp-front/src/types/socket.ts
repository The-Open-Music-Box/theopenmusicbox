/**
 * Socket Event Type Definitions
 * Provides type safety for all socket.io events used in the application
 */

export interface SocketProgressData {
  session_id: string;
  progress: number;
  chunk_index?: number;
  file_name?: string;
}

export interface SocketCompleteData {
  session_id: string;
  file_id?: string;
  filename: string;
  playlist_id?: string;
}

export interface SocketErrorData {
  session_id: string;
  error: string;
  code?: string;
  context?: string;
}

export interface SocketUploadStatusData {
  session_id: string;
  status: 'pending' | 'uploading' | 'processing' | 'complete' | 'error';
  progress?: number;
  error?: string;
}

/**
 * Socket event handler types
 */
export type SocketProgressHandler = (data: SocketProgressData) => void;
export type SocketCompleteHandler = (data: SocketCompleteData) => void;
export type SocketErrorHandler = (data: SocketErrorData) => void;
export type SocketStatusHandler = (data: SocketUploadStatusData) => void;

/**
 * Generic socket event handler
 */
export type SocketEventHandler<T = unknown> = (data: T) => void;

/**
 * Type-safe socket event handler that accepts unknown data and casts it
 */
export function createTypedSocketHandler<T>(handler: (data: T) => void): SocketEventHandler {
  return (data: unknown) => {
    handler(data as T);
  };
}

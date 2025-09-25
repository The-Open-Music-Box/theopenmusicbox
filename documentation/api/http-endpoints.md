# HTTP API Reference - The Open Music Box

## Overview

The Open Music Box provides a comprehensive REST API built with FastAPI that follows modern API design principles. All endpoints return standardized JSON responses with consistent error handling and validation.

## Base Configuration

| Environment | Base URL | Description |
|-------------|----------|-------------|
| **Development** | `http://localhost:5004` | Local development server |
| **Production** | `http://[raspberry-pi-ip]:5004` | Raspberry Pi deployment |

## Authentication

Currently, the API operates without authentication for local network use. Future versions may include optional authentication for enhanced security.

## Response Format

### Success Responses
```json
{
  "status": "success",
  "message": "Operation completed successfully",
  "data": { /* Response payload */ },
  "server_seq": 12345,
  "timestamp": 1640995200000
}
```

### Error Responses
```json
{
  "status": "error",
  "message": "Human-readable error message",
  "error_type": "validation_error|not_found|conflict|rate_limit_exceeded",
  "details": { /* Error context */ },
  "timestamp": 1640995200000,
  "request_id": "abc123"
}
```

## Data Models

### Core Entities

#### Track
```typescript
interface Track {
  id: string;                    // UUID
  title: string;                 // Display name
  filename: string;              // Original filename
  duration_ms: number;           // Duration in milliseconds
  file_path: string;             // Server file location
  file_hash?: string;            // SHA-256 hash
  file_size?: number;            // Size in bytes
  artist?: string;               // Optional artist metadata
  album?: string;                // Optional album metadata
  track_number?: number;         // Optional track number
  play_count: number;            // Usage statistics
  created_at: string;            // ISO timestamp
  updated_at?: string;           // ISO timestamp
  server_seq: number;            // Sequence number
}
```

#### Playlist
```typescript
interface Playlist {
  id: string;                    // UUID
  title: string;                 // Display name
  description: string;           // Optional description
  nfc_tag_id: string | null;     // Associated NFC tag
  tracks: Track[];               // Array of tracks
  track_count: number;           // Number of tracks
  created_at: string;            // ISO timestamp
  updated_at?: string;           // ISO timestamp
  server_seq: number;            // Global sequence
  playlist_seq: number;          // Playlist-specific sequence
}
```

#### PlayerState
```typescript
interface PlayerState {
  is_playing: boolean;           // Current playback state
  state: PlaybackState;          // Detailed state enum
  active_playlist_id: string | null;  // Currently loaded playlist
  active_playlist_title: string | null;  // Playlist display name
  active_track_id: string | null;     // Currently playing track
  active_track: Track | null;          // Complete track object
  position_ms: number;                 // Playback position
  duration_ms: number;                 // Track duration
  track_index: number;                 // Current track index (0-based)
  track_count: number;                 // Total tracks in playlist
  can_prev: boolean;                   // Previous track available
  can_next: boolean;                   // Next track available
  volume: number;                      // Volume level (0-100)
  muted: boolean;                      // Mute state
  server_seq: number;                  // Sequence number
  error_message?: string;              // Error details if any
}

enum PlaybackState {
  PLAYING = "playing",
  PAUSED = "paused",
  STOPPED = "stopped",
  LOADING = "loading",
  ERROR = "error"
}
```

## API Endpoints

### Playlist Management

#### List Playlists
```http
GET /api/playlists
```

**Query Parameters:**
- `page?: number` - Page number (default: 1)
- `limit?: number` - Items per page (default: 50, max: 100)

**Response:**
```json
{
  "status": "success",
  "message": "Playlists retrieved successfully",
  "data": {
    "playlists": [/* PlaylistLite[] */],
    "page": 1,
    "total": 25,
    "limit": 50
  }
}
```

#### Get Specific Playlist
```http
GET /api/playlists/{playlist_id}
```

**Response:**
```json
{
  "status": "success",
  "message": "Playlist retrieved successfully",
  "data": {
    "playlist": {/* Complete Playlist object with tracks */}
  }
}
```

#### Create Playlist
```http
POST /api/playlists/
```

**Request Body:**
```json
{
  "title": "My New Playlist",
  "description": "Optional description",
  "client_op_id": "optional-operation-id"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Playlist created successfully",
  "data": {
    "playlist": {/* Complete Playlist object */}
  }
}
```

#### Update Playlist
```http
PUT /api/playlists/{playlist_id}
```

**Request Body:**
```json
{
  "title": "Updated Title",
  "description": "Updated description",
  "client_op_id": "optional-operation-id"
}
```

#### Delete Playlist
```http
DELETE /api/playlists/{playlist_id}
```

**Request Body:**
```json
{
  "client_op_id": "optional-operation-id"
}
```

#### Start Playlist Playback
```http
POST /api/playlists/{playlist_id}/start
```

**Request Body:**
```json
{
  "client_op_id": "optional-operation-id"
}
```

**Response:** Returns complete `PlayerState` object

#### Play Specific Track
```http
POST /api/playlists/{playlist_id}/play/{track_number}
```

**Parameters:**
- `track_number` - 1-based track index in playlist

**Response:** Returns complete `PlayerState` object

### Player Control

#### Get Player Status
```http
GET /api/player/status
```

**Response:** Returns complete `PlayerState` object

#### Toggle Play/Pause
```http
POST /api/player/toggle
```

**Request Body:**
```json
{
  "client_op_id": "optional-operation-id"
}
```

**Response:** Returns updated `PlayerState` object

#### Stop Playback
```http
POST /api/player/stop
```

**Response:** Returns updated `PlayerState` object

#### Next Track
```http
POST /api/player/next
```

**Response:** Returns updated `PlayerState` object

#### Previous Track
```http
POST /api/player/previous
```

**Response:** Returns updated `PlayerState` object

#### Seek to Position
```http
POST /api/player/seek
```

**Request Body:**
```json
{
  "position_ms": 45000,
  "client_op_id": "optional-operation-id"
}
```

**Response:** Returns updated `PlayerState` object

#### Set Volume
```http
POST /api/player/volume
```

**Request Body:**
```json
{
  "volume": 75,
  "client_op_id": "optional-operation-id"
}
```

**Response:** Returns updated `PlayerState` object

### File Upload System

#### Initialize Upload Session
```http
POST /api/playlists/{playlist_id}/uploads/session
```

**Request Body:**
```json
{
  "filename": "song.mp3",
  "file_size": 5242880,
  "chunk_size": 1048576
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Upload session created",
  "data": {
    "session_id": "uuid-here",
    "chunk_size": 1048576
  }
}
```

#### Upload File Chunk
```http
PUT /api/playlists/{playlist_id}/uploads/{session_id}/chunks/{chunk_index}
```

**Request Body:** `FormData` with chunk binary data

**Response:**
```json
{
  "status": "success",
  "message": "Chunk uploaded successfully",
  "data": {
    "progress": 45.5
  }
}
```

#### Finalize Upload
```http
POST /api/playlists/{playlist_id}/uploads/{session_id}/finalize
```

**Request Body:**
```json
{
  "client_op_id": "optional-operation-id",
  "file_hash": "optional-sha256-hash"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "File uploaded and processed successfully",
  "data": {
    "track": {/* Complete Track object */}
  }
}
```

#### Get Upload Status
```http
GET /api/playlists/{playlist_id}/uploads/{session_id}
```

**Response:**
```json
{
  "status": "success",
  "message": "Upload status retrieved",
  "data": {
    "upload_status": {
      "session_id": "uuid",
      "filename": "song.mp3",
      "file_size": 5242880,
      "bytes_uploaded": 2621440,
      "progress_percent": 50.0,
      "chunks_total": 5,
      "chunks_uploaded": 2,
      "status": "uploading",
      "created_at": "2025-01-01T12:00:00Z",
      "updated_at": "2025-01-01T12:05:00Z"
    }
  }
}
```

### NFC Tag Management

#### Associate Tag with Playlist
```http
POST /api/nfc/associate
```

**Request Body:**
```json
{
  "playlist_id": "playlist-uuid",
  "tag_id": "nfc-tag-id",
  "client_op_id": "optional-operation-id"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "NFC tag associated successfully",
  "data": {
    "association": {
      "tag_id": "nfc-tag-id",
      "playlist_id": "playlist-uuid",
      "playlist_title": "My Playlist",
      "created_at": "2025-01-01T12:00:00Z"
    }
  }
}
```

#### Remove Tag Association
```http
DELETE /api/nfc/associate/{tag_id}
```

**Request Body:**
```json
{
  "client_op_id": "optional-operation-id"
}
```

#### Get NFC Reader Status
```http
GET /api/nfc/status
```

**Response:**
```json
{
  "status": "success",
  "message": "NFC reader status retrieved",
  "data": {
    "reader_available": true,
    "scanning": false
  }
}
```

#### Start NFC Scan Session
```http
POST /api/nfc/scan
```

**Request Body:**
```json
{
  "timeout_ms": 60000
}
```

**Response:**
```json
{
  "status": "success",
  "message": "NFC scan session started",
  "data": {
    "scan_id": "scan-uuid"
  }
}
```

### YouTube Integration

#### Download from YouTube URL
```http
POST /api/youtube/download
```

**Request Body:**
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "playlist_id": "target-playlist-uuid",
  "client_op_id": "optional-operation-id"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "YouTube download started",
  "data": {
    "task_id": "download-task-uuid"
  }
}
```

#### Get Download Progress
```http
GET /api/youtube/status/{task_id}
```

**Response:**
```json
{
  "task_id": "download-task-uuid",
  "status": "downloading",
  "progress_percent": 75.5,
  "current_step": "Converting audio format",
  "estimated_time_remaining": 30000
}
```

#### Search YouTube Videos
```http
GET /api/youtube/search?query=search+terms&max_results=10
```

**Response:**
```json
{
  "status": "success",
  "message": "Search completed successfully",
  "data": {
    "results": [
      {
        "id": "VIDEO_ID",
        "title": "Video Title",
        "duration_ms": 180000,
        "thumbnail_url": "https://thumbnail-url",
        "channel": "Channel Name",
        "view_count": 1000000
      }
    ]
  }
}
```

## Error Handling

### HTTP Status Codes

| Status | Error Type | Description |
|--------|------------|-------------|
| 400 | `validation_error` | Invalid request data or parameters |
| 400 | `bad_request` | General client error |
| 404 | `not_found` | Resource not found |
| 409 | `conflict` | Resource conflict (duplicate names, etc.) |
| 429 | `rate_limit_exceeded` | Too many requests |
| 500 | `internal_error` | Server error |
| 503 | `service_unavailable` | Backend service unavailable |

### Rate Limiting

| Endpoint Category | Window | Max Requests |
|------------------|--------|--------------|
| Player Control | 60s | 30 requests |
| File Uploads | 60s | 10 requests |
| YouTube Downloads | 300s | 5 requests |

### Client Operation IDs

Most endpoints accept an optional `client_op_id` parameter for operation deduplication and tracking. This prevents duplicate operations and enables better error handling.

## Pagination

List endpoints support cursor-based pagination:

```json
{
  "data": {
    "items": [/* Results */],
    "page": 1,
    "limit": 50,
    "total": 150,
    "has_next": true,
    "has_prev": false
  }
}
```

## Versioning

The current API version is v1. Future versions will be accessible via URL versioning:
- Current: `/api/...`
- Future: `/api/v2/...`

This API reference covers all production endpoints. Development and debugging endpoints are documented separately in the development guide.
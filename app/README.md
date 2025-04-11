# TheMusicBox API Documentation

## Table of Contents
1. [Base Configuration](#base-configuration)
2. [REST API Endpoints](#rest-api-endpoints)
3. [WebSocket Events](#websocket-events)
4. [NFC Workflow](#nfc-workflow)
5. [Error Handling](#error-handling)

## Base Configuration

```javascript
const BASE_URL = "http://tmbdev.local:5005/api"
const WS_URL = "ws://tmbdev.local:5005/socket.io/?EIO=4&transport=websocket"
```

## REST API Endpoints

### Playlist Management

#### Get All Playlists
```http
GET /api/playlist
```
**Response:**
```json
{
  "playlists": [
    {
      "id": "string",
      "title": "string",
      "tracks": []
    }
  ]
}
```

#### Create Playlist
```http
POST /api/playlist
```
**Body:**
```json
{
  "title": "string"
}
```
**Response:**
```json
{
  "playlist": {
    "id": "string",
    "title": "string",
    "tracks": []
  }
}
```

#### Delete Playlist
```http
DELETE /api/playlist/{playlist_id}
```
**Response:** `204 No Content`

### Playlist Control

#### Play Playlist
```http
POST /api/playlist/{playlist_id}/play
```
**Response:**
```json
{
  "status": "playing",
  "playlist_id": "string"
}
```

#### Control Commands
```http
POST /api/playlist/control/{command}
```
Available commands:
- `play`: Resume playback
- `pause`: Pause playback
- `stop`: Stop playback
- `next`: Next track
- `previous`: Previous track

**Response:**
```json
{
  "status": "string",
  "message": "string"
}
```

### NFC Management

#### Get NFC Mapping
```http
GET /api/playlists
```
**Response:**
```json
[
  {
    "id": "string",
    "type": "playlist",
    "title": "string",
    "tag_ids": ["string"]
  }
]
```

#### Start NFC Listening
```http
POST /api/nfc/listen/{playlist_id}
```
**Response:**
```json
{
  "status": "waiting",
  "message": "Waiting for NFC tag"
}
```

#### Simulate NFC Tag (Development Only)
```http
POST /api/nfc/simulate_tag
```
**Body:**
```json
{
  "tag_id": "string"
}
```
**Response:**
```json
{
  "status": "string",
  "message": "string"
}
```

#### Override NFC Tag Association
```http
POST /api/nfc/override_tag
```
**Body:**
```json
{
  "tag_id": "string",
  "new_playlist_id": "string"
}
```
**Response:**
```json
{
  "status": "success",
  "message": "Tag association overridden successfully"
}
```

## WebSocket Events

### Connection Events
- `connect`: Connection established
- `disconnect`: Connection closed

### Playback Status Events
```json
{
  "type": "playback_status",
  "data": {
    "status": "playing|paused|stopped",
    "current_track": {
      "title": "string",
      "artist": "string",
      "duration": number
    }
  }
}
```

### Track Progress Events
```json
{
  "type": "track_progress",
  "data": {
    "elapsed": number,
    "total": number
  }
}
```

### NFC Events
```json
{
  "type": "nfc_status",
  "data": {
    "status": "waiting|success|error",
    "message": "string",
    "requires_override": boolean,
    "current_playlist": {
      "id": "string",
      "title": "string"
    }
  }
}
```

## NFC Workflow

### Standard Association Flow
1. Frontend initiates NFC listening for a playlist
2. Backend starts listening for NFC tags
3. When a tag is detected:
   - If tag is new: Associate with playlist
   - If tag is used: Send error with override option

### Override Flow
1. Tag is detected and already associated
2. Backend sends error with `requires_override: true`
3. Frontend displays override confirmation
4. If user confirms:
   - Send override request
   - Previous association is removed
   - New association is created

### Example Frontend Implementation
```javascript
// Start listening for NFC
async function startNFCListening(playlistId) {
  const response = await fetch(`${BASE_URL}/nfc/listen/${playlistId}`, {
    method: 'POST'
  });
  return response.json();
}

// Handle NFC events
socket.on('nfc_status', (data) => {
  if (data.status === 'error' && data.requires_override) {
    // Show override confirmation dialog
    if (confirmOverride()) {
      overrideTagAssociation(data.tag_id, currentPlaylistId);
    }
  }
});

// Override tag association
async function overrideTagAssociation(tagId, newPlaylistId) {
  const response = await fetch(`${BASE_URL}/nfc/override_tag`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      tag_id: tagId,
      new_playlist_id: newPlaylistId
    })
  });
  return response.json();
}
```

## Error Handling

### HTTP Status Codes
- `200`: Success
- `201`: Created
- `204`: No Content
- `400`: Bad Request
- `404`: Not Found
- `409`: Conflict (e.g., tag already associated)
- `500`: Internal Server Error

### Error Response Format
```json
{
  "status": "error",
  "message": "string",
  "code": "string",
  "details": {}
}
```

### Common Error Codes
- `TAG_ALREADY_ASSOCIATED`: NFC tag is already associated with another playlist
- `TAG_READ_ERROR`: Error reading NFC tag
- `INVALID_PLAYLIST`: Playlist ID is invalid or not found
- `PLAYBACK_ERROR`: Error during playback control
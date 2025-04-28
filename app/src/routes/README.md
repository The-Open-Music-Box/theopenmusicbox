# NFC-Triggered Multimedia Player Backend API Documentation

## Table of Contents
1. [Introduction](#introduction)
2. [System Overview](#system-overview)
3. [Authentication](#authentication)
4. [API Endpoints](#api-endpoints)
    - [NFC Routes](#nfc-routes)
    - [Playlist Routes](#playlist-routes)
    - [YouTube Routes](#youtube-routes)
    - [Web Routes](#web-routes)
    - [WebSocket Events](#websocket-events)
5. [Troubleshooting](#troubleshooting)

---

## Introduction

This API enables integration with a Python-based multimedia player system enhanced with NFC reader technology. The backend allows developers to manage playlists, trigger playback via NFC tags, and interact with the system through both RESTful and WebSocket interfaces. It is designed for use on a Raspberry Pi but can also run in a mocked environment for testing.

## System Overview

- **NFC Reader Integration:** Detects NFC tags and triggers associated playlists.
- **Playlist Management:** Create, update, delete, and play playlists and tracks.
- **WebSocket Support:** Real-time updates for playback progress and system events.
- **Mock/Production Modes:** Supports both real hardware and mocked environments for development/testing.

## Authentication

Currently, the API does not enforce authentication.

## API Endpoints

### NFC Routes

| Method | Path                               | Description                                  |
|--------|------------------------------------|----------------------------------------------|
| POST   | /api/nfc/associate/initiate        | Initiate NFC association for a playlist      |
| POST   | /api/nfc/associate/complete        | Complete association after tag scan          |
| POST   | /api/nfc/disassociate              | Disassociate an NFC tag from a playlist      |
| GET    | /api/nfc/status                    | Get current NFC association/listening status |
| POST   | /api/nfc/listen/<playlist_id>      | Start NFC listening for a playlist           |
| POST   | /api/nfc/stop                      | Stop current NFC listening                   |
| POST   | /api/nfc/simulate_tag              | Simulate NFC tag detection (testing)         |

#### 1. Initiate NFC Association
- **POST /api/nfc/associate/initiate**
- **Purpose:** Begin association mode for a playlist (activates NFC reader)
- **Request Body:**
  ```json
  { "playlist_id": "string" }
  ```
- **Response:**
  - 200: `{ "status": "association_initiated", "playlist_id": "string" }`
  - 400: `{ "error": "playlist_id is required" }`
  - 409: `{ "error": "NFC association already in progress" }`

#### 2. Complete NFC Association
- **POST /api/nfc/associate/complete**
- **Purpose:** Complete association after tag scan
- **Request Body:**
  ```json
  { "playlist_id": "string", "nfc_tag": "string" }
  ```
- **Response:**
  - 200: `{ "status": "association_complete", "playlist_id": "string", "nfc_tag": "string" }`
  - 400: `{ "error": "playlist_id and nfc_tag are required" }`
  - 409: `{ "error": "NFC tag already associated" }`
  - 404: `{ "error": "Playlist not found" }`

#### 3. Disassociate NFC Tag
- **POST /api/nfc/disassociate**
- **Purpose:** Remove association between an NFC tag and a playlist
- **Request Body:**
  ```json
  { "playlist_id": "string", "nfc_tag": "string" }
  ```
- **Response:**
  - 200: `{ "status": "disassociated", "playlist_id": "string", "nfc_tag": "string" }`
  - 400: `{ "error": "playlist_id and nfc_tag are required" }`
  - 404: `{ "error": "Tag not associated with playlist" }`

#### 4. Get NFC Status
- **GET /api/nfc/status**
- **Purpose:** Retrieve current NFC association/listening status
- **Response:**
  - 200: `{ ...status object... }`

#### 5. Start NFC Listening
- **POST /api/nfc/listen/<playlist_id>**
- **Purpose:** Start listening for NFC tags for a specific playlist
- **Response:**
  - 200: `{ "status": "success", "message": "NFC listening started" }`
  - 404: `{ "status": "error", "message": "Playlist not found" }`
  - 409: `{ "status": "error", "message": "An NFC listening session is already active" }`

#### 6. Stop NFC Listening
- **POST /api/nfc/stop**
- **Purpose:** Stop current NFC listening session
- **Response:**
  - 200: `{ "status": "success", "message": "NFC listening stopped" }`

#### 7. Simulate NFC Tag Detection
- **POST /api/nfc/simulate_tag**
- **Purpose:** Simulate tag detection (for testing, no real hardware required)
- **Request Body:**
  ```json
  { "tag_id": "string" }
  ```
- **Response:**
  - 200: `{ "status": "success", "message": "Tag <tag_id> processed successfully" }`
  - 409: `{ "status": "error", "message": "Tag not processed or already associated" }`

---

### Playlist Routes

| Method | Path                                             | Description                         |
|--------|--------------------------------------------------|-------------------------------------|
| GET    | /api/playlists                                   | List all playlists                  |
| GET    | /api/playlists/<playlist_id>                     | Get playlist details                |
| DELETE | /api/playlists/<playlist_id>                     | Delete a playlist                   |
| POST   | /api/playlists                                   | Create a new playlist               |
| POST   | /api/playlists/<playlist_id>/tracks              | Upload tracks to playlist           |
| PATCH  | /api/playlists/<playlist_id>/tracks/reorder      | Reorder tracks in playlist          |
| DELETE | /api/playlists/<playlist_id>/tracks/<track_id>   | Delete a track from playlist        |
| POST   | /api/playlists/<playlist_id>/start               | Start playing a playlist            |
| POST   | /api/playlists/<playlist_id>/play/<track_number> | Play a specific track in playlist   |
| POST   | /api/playlists/control                           | Control playback (play/pause/stop)  |
| POST   | /api/playlists/<playlist_id>/upload              | Upload files to playlist            |
| DELETE | /api/playlists/<playlist_id>/tracks              | Delete multiple tracks from playlist|

_**For each endpoint, the request/response structure follows standard RESTful conventions with JSON bodies for POST/PATCH requests and JSON responses.**_

#### Example: Create Playlist
- **POST /api/playlists**
- **Request Body:**
  ```json
  { "title": "My Playlist", "description": "string" }
  ```
- **Response:**
  - 200: `{ "status": "success", "playlist": { ... } }`
  - 400: `{ "error": "..." }`

---

### YouTube Routes

| Method | Path                  | Description                       |
|--------|-----------------------|-----------------------------------|
| POST   | /api/youtube/download | Download tracks from YouTube      |

#### Download YouTube Track
- **POST /api/youtube/download**
- **Request Body:**
  ```json
  { "url": "https://youtube.com/..." }
  ```
- **Response:**
  - 200: `{ ...result object... }`
  - 400: `{ "error": "Invalid YouTube URL" }`
  - 500: `{ "error": "Download failed: ..." }`

---

### Web Routes

| Method | Path         | Description                |
|--------|--------------|----------------------------|
| GET    | /            | Serve frontend application |
| GET    | /health      | Health check endpoint      |

#### Health Check
- **GET /health**
- **Response:**
  - 200: `{ "status": "ok", "components": { ... } }`
  - 500: `{ "status": "error", "message": "..." }`

---

### WebSocket Events

- **Endpoint:** (WebSocket connection, typically at `/socket.io/`)
- **Events:**
    - `track_progress`: Real-time updates on track playback progress
    - `upload_progress`: File upload progress events
    - `connection_status`: Connection status updates on connect/disconnect
- **Example:**
  ```js
  socket.on('track_progress', data => { /* handle playback progress */ });
  socket.on('upload_progress', data => { /* handle upload progress */ });
  socket.on('connection_status', data => { /* handle connection status */ });
  ```

---

## Troubleshooting

- **400 Bad Request:** Ensure all required fields are provided and request bodies are valid JSON.
- **404 Not Found:** Resource does not exist (e.g., playlist or tag not found).
- **409 Conflict:** Operation not allowed due to current state (e.g., NFC session already active).
- **500 Internal Server Error:** Check server logs for more details.
- **WebSocket Issues:** Ensure the frontend is connecting to the correct WebSocket endpoint and that the server is running.

---

**For further details, review the backend source code or contact the backend development team.**
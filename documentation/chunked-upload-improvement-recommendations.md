# Chunked Upload System Improvement Recommendations

**Date:** 2025-07-09
**Author:** Cascade AI Assistant
**Version:** 1.0

## Table of Contents

1. [Introduction](#introduction)
2. [Current Implementation Overview](#current-implementation-overview)
3. [Identified Inconsistencies](#identified-inconsistencies)
   - [API Route Inconsistencies](#api-route-inconsistencies)
   - [Parameter Inconsistencies](#parameter-inconsistencies)
   - [Implementation Flow Inconsistencies](#implementation-flow-inconsistencies)
4. [Detailed Recommendations](#detailed-recommendations)
   - [API Route Standardization](#api-route-standardization)
   - [Documentation Improvements](#documentation-improvements)
   - [Parameter Naming Consistency](#parameter-naming-consistency)
   - [Session Management Enhancements](#session-management-enhancements)
   - [Error Handling Improvements](#error-handling-improvements)
   - [Performance Optimizations](#performance-optimizations)
5. [Implementation Priority](#implementation-priority)
6. [Testing Strategy](#testing-strategy)
7. [Migration Path](#migration-path)
8. [Conclusion](#conclusion)

## Introduction

This document presents a comprehensive analysis of the current chunked upload system implementation in TheOpenMusicBox and provides detailed recommendations for improvements. The primary goal is to resolve inconsistencies between the frontend and backend implementations, enhance system reliability, and improve the developer experience.

The chunked upload system allows large audio files to be uploaded in manageable chunks, providing progress tracking and resilience against connection issues. While the current implementation provides the core functionality, several inconsistencies and potential improvements have been identified through code review.

## Current Implementation Overview

### Frontend Implementation

The frontend implementation includes:

1. **Core Components:**
   - `useChunkedUpload.ts`: A composable that manages the chunking logic
   - `ChunkedPlaylistUploader.vue`: UI component for file selection and progress display
   - `uploadStore.ts`: Centralized store for tracking upload state
   - `eventBus.ts`: Event bus for cross-component communication

2. **API Integration:**
   - New routes added to `apiRoutes.ts` for chunked upload operations
   - Extended `dataService.ts` and `realApiService.ts` with methods for chunked uploads
   - Socket.IO integration for real-time progress updates

3. **Workflow:**
   - Files are split into 1MB chunks
   - Upload sessions are initialized with file metadata
   - Chunks are uploaded sequentially
   - Upload is finalized when all chunks are received
   - Real-time progress updates via Socket.IO

### Backend Implementation

The backend implementation includes:

1. **Core Components:**
   - `ChunkedUploadService`: Manages chunked upload sessions, file assembly, and cleanup
   - `UploadService`: Handles file storage and metadata extraction
   - Socket.IO server integration for progress events

2. **API Routes:**
   - `/api/playlists/uploads/session`: Initialize upload session
   - `/api/playlists/{playlist_id}/upload/chunk`: Upload individual chunks
   - `/api/playlists/{playlist_id}/upload/finalize`: Finalize an upload
   - Session status checking functionality

3. **Session Management:**
   - In-memory tracking of active upload sessions
   - Temporary storage for chunks
   - Session cleanup for completed or failed uploads

## Identified Inconsistencies

### API Route Inconsistencies

1. **Session Initialization Endpoint:**
   - **Frontend:** Configured as `/api/playlists/{id}/upload/init` but comments acknowledge using `/api/playlists/uploads/session`
   - **Backend:** Implemented as `/api/playlists/uploads/session`
   - **Problem:** Inconsistent URL structure and REST pattern violation (playlist ID not included)

2. **Upload Status Endpoint:**
   - **Frontend:** Uses `/api/uploads/session/${sessionId}`
   - **Backend:** No direct route matching this pattern
   - **Problem:** Missing or mismatched route implementation

3. **Chunk Upload Endpoint:**
   - **Frontend:** Uses `/api/playlists/${id}/upload/chunk`
   - **Backend:** Matches as `/api/playlists/{playlist_id}/upload/chunk`
   - **Problem:** No direct inconsistency, but naming pattern differs from session initialization

4. **Finalization Endpoint:**
   - **Frontend:** Uses `/api/playlists/${id}/upload/finalize`
   - **Backend:** Matches as `/api/playlists/{playlist_id}/upload/finalize`
   - **Problem:** No direct inconsistency, but naming pattern differs from session initialization

### Parameter Inconsistencies

1. **Session Initialization Parameters:**
   - **Frontend:** Uses camelCase properties (`filename`, `total_size`, `total_chunks`)
   - **Backend:** Expects snake_case parameters (`filename`, `total_size`, `total_chunks`)
   - **Problem:** Inconsistent naming convention, though functionally compatible

2. **Chunk Upload Parameters:**
   - **Frontend:** Sends `FormData` with `session_id`, `chunk_index`, and file chunk
   - **Backend:** Expects `session_id`, `chunk_index` as form fields and `file` as upload
   - **Problem:** No direct inconsistency, but documentation is lacking

### Implementation Flow Inconsistencies

1. **Session Management:**
   - **Backend:** Uses in-memory dictionary (`active_uploads`)
   - **Problem:** Sessions are lost on server restart

2. **Error Handling:**
   - **Backend:** Throws specific exceptions (`InvalidFileError`, `ProcessingError`)
   - **Frontend:** Generic error handling
   - **Problem:** Error specificity and context may be lost

3. **Socket.IO Events:**
   - **Backend:** Emits `upload_progress`, `upload_complete`, `upload_error`
   - **Frontend:** Must listen for exact event names
   - **Problem:** Limited documentation of event structures

## Detailed Recommendations

### API Route Standardization

1. **Implement Consistent REST Pattern:**

   ```
   # Session Initialization
   POST /api/playlists/{playlist_id}/uploads/session
   
   # Chunk Upload
   POST /api/playlists/{playlist_id}/uploads/{session_id}/chunks/{chunk_index}
   
   # Upload Status
   GET /api/playlists/{playlist_id}/uploads/{session_id}
   
   # Upload Finalization
   POST /api/playlists/{playlist_id}/uploads/{session_id}/finalize
   ```

2. **Route Implementation Plan:**

   - **Backend Changes:**
     ```python
     # Update in playlist_routes.py
     @self.router.post("/{playlist_id}/uploads/session")
     async def create_upload_session(
         self, playlist_id: str, filename: str, total_chunks: int, total_size: int
     ):
         # Implementation
         pass
     
     @self.router.post("/{playlist_id}/uploads/{session_id}/chunks/{chunk_index}")
     async def upload_chunk(
         self, playlist_id: str, session_id: str, chunk_index: int, file: UploadFile
     ):
         # Implementation
         pass
     
     @self.router.get("/{playlist_id}/uploads/{session_id}")
     async def get_upload_status(
         self, playlist_id: str, session_id: str
     ):
         # Implementation
         pass
     
     @self.router.post("/{playlist_id}/uploads/{session_id}/finalize")
     async def finalize_upload(
         self, playlist_id: str, session_id: str
     ):
         # Implementation
         pass
     ```

   - **Frontend Changes:**
     ```typescript
     // Update in apiRoutes.ts
     PLAYLIST_UPLOAD_INIT: (id: string) => `/api/playlists/${id}/uploads/session`,
     PLAYLIST_UPLOAD_CHUNK: (id: string, sessionId: string, chunkIndex: number) => 
       `/api/playlists/${id}/uploads/${sessionId}/chunks/${chunkIndex}`,
     PLAYLIST_UPLOAD_STATUS: (id: string, sessionId: string) => 
       `/api/playlists/${id}/uploads/${sessionId}`,
     PLAYLIST_UPLOAD_FINALIZE: (id: string, sessionId: string) => 
       `/api/playlists/${id}/uploads/${sessionId}/finalize`,
     ```

### Documentation Improvements

1. **Update API Documentation:**

   Add a dedicated section to `routes-api.md` for chunked uploads:

   ```markdown
   ## Chunked Upload System
   
   ### POST `/api/playlists/{playlist_id}/uploads/session`
   - **Description**: Initialize a chunked upload session
   - **Parameters Path**:
     - `playlist_id` *(str, required)*: ID of the playlist
   - **Payload**:
   ```json
   {
     "filename": "example.mp3",
     "total_size": 5242880,
     "total_chunks": 5
   }
   ```
   - **Response**:
   ```json
   {
     "session_id": "550e8400-e29b-41d4-a716-446655440000",
     "expires_at": "2025-07-10T15:30:00Z"
   }
   ```
   
   ### POST `/api/playlists/{playlist_id}/uploads/{session_id}/chunks/{chunk_index}`
   - **Description**: Upload a single chunk of a file
   - **Parameters Path**:
     - `playlist_id` *(str, required)*: ID of the playlist
     - `session_id` *(str, required)*: ID of the upload session
     - `chunk_index` *(int, required)*: Index of the chunk (0-based)
   - **Form Data**:
     - `file` *(file, required)*: The binary chunk data
   - **Response**:
   ```json
   {
     "status": "success",
     "chunk_index": 2,
     "received_chunks": 3,
     "total_chunks": 5,
     "progress": 60.0
   }
   ```
   
   ### GET `/api/playlists/{playlist_id}/uploads/{session_id}`
   - **Description**: Get the status of an upload session
   - **Parameters Path**:
     - `playlist_id` *(str, required)*: ID of the playlist
     - `session_id` *(str, required)*: ID of the upload session
   - **Response**:
   ```json
   {
     "filename": "example.mp3",
     "total_chunks": 5,
     "received_chunks": 3,
     "current_size": 3145728,
     "total_size": 5242880,
     "progress": 60.0,
     "complete": false
   }
   ```
   
   ### POST `/api/playlists/{playlist_id}/uploads/{session_id}/finalize`
   - **Description**: Finalize an upload session after all chunks are uploaded
   - **Parameters Path**:
     - `playlist_id` *(str, required)*: ID of the playlist
     - `session_id` *(str, required)*: ID of the upload session
   - **Response**:
   ```json
   {
     "status": "success",
     "filename": "example.mp3",
     "metadata": {
       "title": "Example Song",
       "artist": "Example Artist",
       "album": "Example Album",
       "duration": 240.5
     }
   }
   ```
   ```

2. **Document Socket.IO Events:**

   Add comprehensive documentation for Socket.IO events:

   ```markdown
   ## Socket.IO Events for Chunked Uploads
   
   The server emits the following events during chunked upload operations:
   
   ### `upload_progress`
   
   Emitted when a chunk is successfully processed or when progress is updated.
   
   ```json
   {
     "playlist_id": "playlist-123",
     "session_id": "550e8400-e29b-41d4-a716-446655440000",
     "filename": "example.mp3",
     "chunk_index": 2,
     "total_chunks": 5,
     "progress": 60.0,
     "complete": false
   }
   ```
   
   ### `upload_complete`
   
   Emitted when an upload is successfully finalized and the file is processed.
   
   ```json
   {
     "playlist_id": "playlist-123",
     "session_id": "550e8400-e29b-41d4-a716-446655440000",
     "filename": "example.mp3",
     "metadata": {
       "title": "Example Song",
       "artist": "Example Artist",
       "album": "Example Album",
       "duration": 240.5
     }
   }
   ```
   
   ### `upload_error`
   
   Emitted when an error occurs during upload processing.
   
   ```json
   {
     "playlist_id": "playlist-123",
     "session_id": "550e8400-e29b-41d4-a716-446655440000",
     "filename": "example.mp3",
     "error": "Error message description",
     "error_code": "FILE_TOO_LARGE", // Optional error code
     "chunk_index": 2 // Optional, context of where error occurred
   }
   ```
   ```

3. **Create Technical Implementation Documentation:**

   Create a new document `chunked-upload-technical-implementation.md` explaining:
   - Architecture diagram
   - Sequence diagrams for successful and error flows
   - Performance considerations
   - Security considerations
   - Testing approach

### Parameter Naming Consistency

1. **Standardize on Snake Case for API:**

   - **Backend:** Already uses snake_case for parameters
   - **Frontend:** Should convert camelCase to snake_case when sending to API

   ```typescript
   // Example implementation in useChunkedUpload.ts
   
   // Convert from camelCase to snake_case for API requests
   const initializeUpload = async (file: File) => {
     const apiPayload = {
       filename: file.name,
       total_size: file.size,
       total_chunks: Math.ceil(file.size / CHUNK_SIZE)
     };
     
     return await dataService.initUpload(playlistId, apiPayload);
   };
   
   // Convert from snake_case to camelCase when receiving API responses
   const processApiResponse = (response: any) => {
     return {
       sessionId: response.session_id,
       expiresAt: response.expires_at,
       // ...other fields
     };
   };
   ```

2. **Document Naming Conventions:**

   Add a section to a development standards document or API documentation:

   ```markdown
   ## API Parameter Naming Conventions
   
   - **Backend API Parameters:** All API parameters use `snake_case` format
   - **Frontend Variables:** Use `camelCase` for JavaScript/TypeScript variables
   - **Conversion:** Frontend code should convert between formats when communicating with the API
   ```

### Session Management Enhancements

1. **Implement Persistent Session Storage:**

   ```python
   # In ChunkedUploadService
   
   class ChunkedUploadService:
       def __init__(self, config, upload_service=None, session_store=None):
           # ...existing code...
           self.session_store = session_store or FileSystemSessionStore(config)
           
       def create_session(self, filename, total_chunks, total_size):
           # ...existing code...
           # Save session to persistent store
           self.session_store.save_session(session_id, session_data)
           
       def load_session(self, session_id):
           # Load from persistent store
           return self.session_store.get_session(session_id)
           
   class FileSystemSessionStore:
       def __init__(self, config):
           self.sessions_dir = Path(config.upload_folder) / "sessions"
           self.sessions_dir.mkdir(parents=True, exist_ok=True)
           
       def get_session_path(self, session_id):
           return self.sessions_dir / f"{session_id}.json"
           
       def save_session(self, session_id, session_data):
           with open(self.get_session_path(session_id), 'w') as f:
               json.dump(session_data, f)
               
       def get_session(self, session_id):
           path = self.get_session_path(session_id)
           if path.exists():
               with open(path, 'r') as f:
                   return json.load(f)
           return None
           
       def delete_session(self, session_id):
           path = self.get_session_path(session_id)
           if path.exists():
               path.unlink()
   ```

2. **Implement Session Expiry and Cleanup:**

   ```python
   # In ChunkedUploadService
   
   def create_session(self, filename, total_chunks, total_size):
       # ...existing code...
       session_data = {
           # ...existing fields...
           "created_at": time.time(),
           "expires_at": time.time() + (3600 * 24),  # 24 hours from now
       }
       
   def cleanup_expired_sessions(self):
       """Remove expired upload sessions and their temporary files."""
       now = time.time()
       for session_id, session in list(self.active_uploads.items()):
           if now > session.get("expires_at", 0):
               self._cleanup_session(session_id)
               
   def schedule_cleanup(self):
       """Schedule periodic cleanup of expired sessions."""
       # Implementation depends on the task scheduling approach
       # Could use APScheduler, Celery, or similar
   ```

3. **Session Recovery Mechanism:**

   ```python
   # In ChunkedUploadService
   
   def recover_sessions_on_startup(self):
       """Recover active sessions from persistent storage on service startup."""
       try:
           session_files = list(self.sessions_dir.glob("*.json"))
           for session_file in session_files:
               try:
                   with open(session_file, 'r') as f:
                       session_data = json.load(f)
                   
                   # Check if session is not expired
                   if time.time() <= session_data.get("expires_at", 0):
                       session_id = session_file.stem
                       self.active_uploads[session_id] = session_data
                   else:
                       # Clean up expired session
                       self._cleanup_session(session_file.stem)
               except Exception as e:
                   logger.error(f"Error recovering session {session_file}: {e}")
       except Exception as e:
           logger.error(f"Error during session recovery: {e}")
   ```

### Error Handling Improvements

1. **Standardized Error Response Format:**

   Define a consistent error response format:

   ```python
   def api_error_response(error_code, message, details=None, status_code=400):
       """Generate standardized error response."""
       response = {
           "status": "error",
           "error_code": error_code,
           "message": message,
       }
       if details:
           response["details"] = details
       return JSONResponse(content=response, status_code=status_code)
   
   # Example usage
   @self.router.post("/{playlist_id}/uploads/session")
   async def create_upload_session(...):
       try:
           # Implementation
       except InvalidFileError as e:
           return api_error_response(
               "INVALID_FILE", str(e), status_code=400
           )
       except ProcessingError as e:
           return api_error_response(
               "PROCESSING_ERROR", str(e), status_code=500
           )
       except Exception as e:
           return api_error_response(
               "UNKNOWN_ERROR", "An unexpected error occurred", status_code=500
           )
   ```

2. **Frontend Error Handling Enhancement:**

   ```typescript
   // Add to ApiService or similar utility
   
   // Error response type definition
   interface ApiErrorResponse {
     status: string;
     error_code: string;
     message: string;
     details?: any;
   }
   
   // Error class with API error details
   class ApiError extends Error {
     code: string;
     details?: any;
     statusCode: number;
     
     constructor(error: ApiErrorResponse, statusCode: number) {
       super(error.message);
       this.name = 'ApiError';
       this.code = error.error_code;
       this.details = error.details;
       this.statusCode = statusCode;
     }
     
     isInvalidFile(): boolean {
       return this.code === 'INVALID_FILE';
     }
     
     isProcessingError(): boolean {
       return this.code === 'PROCESSING_ERROR';
     }
     
     // Other helper methods based on error codes
   }
   
   // Axios interceptor to standardize error handling
   apiClient.interceptors.response.use(
     response => response,
     error => {
       if (error.response?.data && error.response.data.status === 'error') {
         throw new ApiError(error.response.data, error.response.status);
       }
       throw error;
     }
   );
   
   // Usage in components
   try {
     await dataService.initUpload(playlistId, metadata);
   } catch (error) {
     if (error instanceof ApiError) {
       if (error.isInvalidFile()) {
         // Handle invalid file error
       } else if (error.isProcessingError()) {
         // Handle processing error
       }
     } else {
       // Handle network or other errors
     }
   }
   ```

3. **Client-Side Validation:**

   ```typescript
   // In useChunkedUpload.ts
   
   const validateFile = (file: File): string | null => {
     // Check file type
     if (!file.type.startsWith('audio/')) {
       return 'Le fichier doit être au format audio';
     }
     
     // Check file size
     const maxSize = 500 * 1024 * 1024; // 500 MB
     if (file.size > maxSize) {
       return `La taille du fichier ne doit pas dépasser ${formatSize(maxSize)}`;
     }
     
     // Check file name
     if (!/^[a-zA-Z0-9_\-. ]+$/.test(file.name)) {
       return 'Le nom du fichier contient des caractères non autorisés';
     }
     
     return null;
   };
   
   const processFiles = (files: File[]) => {
     const validFiles = [];
     const errors = [];
     
     for (const file of files) {
       const error = validateFile(file);
       if (error) {
         errors.push(`${file.name}: ${error}`);
       } else {
         validFiles.push(file);
       }
     }
     
     return { validFiles, errors };
   };
   ```

### Performance Optimizations

1. **Parallel Chunk Uploads:**

   ```typescript
   // In useChunkedUpload.ts
   
   const MAX_CONCURRENT_CHUNKS = 3;
   
   const uploadFileChunks = async (file: File, sessionId: string) => {
     const totalChunks = Math.ceil(file.size / CHUNK_SIZE);
     let activeUploads = 0;
     let nextChunkIndex = 0;
     let completedChunks = 0;
     const chunkResults = new Array(totalChunks);
     
     return new Promise<void>((resolve, reject) => {
       const processQueue = async () => {
         // Start new uploads until we reach concurrent limit or run out of chunks
         while (activeUploads < MAX_CONCURRENT_CHUNKS && nextChunkIndex < totalChunks) {
           const chunkIndex = nextChunkIndex++;
           activeUploads++;
           
           uploadChunk(file, sessionId, chunkIndex).then(result => {
             chunkResults[chunkIndex] = result;
             completedChunks++;
             activeUploads--;
             
             // Continue processing queue
             processQueue();
             
             // Check if we're done
             if (completedChunks === totalChunks) {
               resolve();
             }
           }).catch(error => {
             reject(error);
           });
         }
       };
       
       // Start initial batch of uploads
       processQueue();
     });
   };
   ```

2. **Chunked Upload Resume Capability:**

   ```typescript
   // In useChunkedUpload.ts
   
   const resumeUpload = async (sessionId: string, playlistId: string) => {
     try {
       // Get status of the upload session
       const status = await dataService.getUploadStatus(playlistId, sessionId);
       
       // If already complete, skip to finalization
       if (status.complete) {
         return await dataService.finalizeUpload(playlistId, { session_id: sessionId });
       }
       
       // Calculate which chunks still need to be uploaded
       const missingChunks = [];
       for (let i = 0; i < status.total_chunks; i++) {
         if (!status.received_chunks.includes(i)) {
           missingChunks.push(i);
         }
       }
       
       // Upload missing chunks
       for (const chunkIndex of missingChunks) {
         const chunk = getChunkFromFile(file, chunkIndex);
         await uploadChunk(chunk, sessionId, chunkIndex);
       }
       
       // Finalize the upload
       return await dataService.finalizeUpload(playlistId, { session_id: sessionId });
     } catch (error) {
       console.error('Failed to resume upload:', error);
       throw error;
     }
   };
   
   // Function to store upload session IDs in localStorage for potential resume
   const storeUploadSession = (playlistId: string, sessionId: string, filename: string) => {
     const pendingUploads = JSON.parse(localStorage.getItem('pendingUploads') || '{}');
     pendingUploads[sessionId] = {
       playlistId,
       filename,
       timestamp: Date.now()
     };
     localStorage.setItem('pendingUploads', JSON.stringify(pendingUploads));
   };
   ```

3. **Backend Optimizations:**

   ```python
   # In ChunkedUploadService
   
   # Optimize temporary file handling
   def save_chunk(self, session_id, chunk_index, file_content):
       """Save a chunk to disk in the session directory."""
       session = self.active_uploads[session_id]
       chunk_path = session["session_dir"] / f"chunk_{chunk_index:05d}"
       
       # Write chunk directly to disk without loading entire content into memory
       with open(chunk_path, 'wb') as f:
           shutil.copyfileobj(file_content, f)
       
       # Update session state
       session["received_chunks"].append(chunk_index)
       session["current_size"] += os.path.getsize(chunk_path)
       
       # Save session state
       self.session_store.save_session(session_id, session)
       
       return {
           "chunk_index": chunk_index,
           "received_chunks": len(session["received_chunks"]),
           "total_chunks": session["total_chunks"],
           "progress": len(session["received_chunks"]) / session["total_chunks"] * 100
       }
   ```

## Implementation Priority

Based on the recommendations above, we suggest the following implementation priority:

1. **Critical** (High Impact, Low Effort):
   - API Route Standardization
   - Documentation Updates
   - Parameter Naming Consistency

2. **Important** (High Impact, Medium Effort):
   - Error Handling Improvements
   - Session Management Persistence

3. **Enhancement** (Medium Impact, Medium/High Effort):
   - Performance Optimizations
   - Resume Capability

4. **Future** (Lower Impact, Higher Effort):
   - Advanced Analytics and Monitoring
   - Integration with Content Delivery Network

## Testing Strategy

To ensure the improved chunked upload system works reliably, implement the following testing strategy:

1. **Unit Tests:**
   - Test chunk splitting and reassembly logic
   - Test session management functions
   - Test error handling and recovery

2. **Integration Tests:**
   - Test full upload workflow with different file sizes
   - Test concurrent uploads
   - Test error scenarios (network interruption, server restart)

3. **Performance Tests:**
   - Measure upload speeds with different chunk sizes
   - Benchmark parallel vs. sequential uploads
   - Test system under high load

4. **End-to-End Tests:**
   - Automate browser tests with file uploads
   - Validate Socket.IO events and progress updates
   - Test resume capability after page reload

## Migration Path

To ensure a smooth transition to the improved chunked upload system:

1. **Phase 1: Documentation and Planning**
   - Update API documentation
   - Create detailed technical specifications
   - Define test cases

2. **Phase 2: Backend Implementation**
   - Implement new route structure
   - Add persistent session storage
   - Enhance error handling
   - Maintain backward compatibility

3. **Phase 3: Frontend Implementation**
   - Update API client code
   - Enhance error handling
   - Add resume capability
   - Improve progress reporting

4. **Phase 4: Testing and Deployment**
   - Run all test suites
   - Deploy to staging environment
   - Conduct user acceptance testing
   - Deploy to production with monitoring

## Conclusion

The recommendations in this document aim to resolve the identified inconsistencies and enhance the chunked upload system of TheOpenMusicBox. By implementing these changes, the application will benefit from:

1. A more consistent and intuitive API structure
2. Improved error handling and user feedback
3. Enhanced reliability through persistent session management
4. Better performance with parallel uploads and optimization
5. Comprehensive documentation for future development

These improvements will provide a better user experience for uploading large audio files and a more maintainable codebase for developers.
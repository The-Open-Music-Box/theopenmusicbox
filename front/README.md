# The Open Music Box - Frontend

> Frontend for TheOpenMusicBox, a Vue.js application that provides a user interface for managing music playlists, NFC tags, and system settings.

## Table of Contents
- [Architecture Overview](#architecture-overview)
- [Overview](#overview)
- [Project Structure](#project-structure)
- [State Management](#state-management)
- [Development Setup](#development-setup)
- [Build Process](#build-process)
- [Key Components](#key-components)
- [API Integration](#api-integration)
- [WebSocket Integration](#websocket-integration)
- [Configuration](#configuration)
- [Development Patterns](#development-patterns)
- [Testing](#testing)
- [Deployment](#deployment)

## Architecture Overview

The Open Music Box frontend implements a **server-state synchronization architecture** where the client subscribes to authoritative state from the backend and never maintains its own version of the truth.

### Core Design Principles

- **Server-State Pattern**: Frontend subscribes to backend state events, no local authoritative state
- **Reactive UI**: Vue 3 Composition API with Pinia stores for reactive state management
- **Real-time Synchronization**: WebSocket events keep UI synchronized with server state
- **Service Layer Architecture**: Clean separation between API communication and UI components
- **TypeScript Integration**: Full type safety across the application

### Client-Server Communication Flow

```
┌─────────────────┐    HTTP Requests    ┌─────────────────┐
│                 │ ──────────────────► │                 │
│   Vue Frontend  │                     │ FastAPI Backend │
│                 │ ◄────────────────── │                 │
└─────────────────┘   WebSocket Events  └─────────────────┘
        │                                        │
        │                                        │
   ┌─────────┐                              ┌─────────┐
   │ Pinia   │                              │ State   │
   │ Stores  │                              │ Manager │
   └─────────┘                              └─────────┘
```

### State Synchronization Pattern

1. **User Action**: User interacts with UI component
2. **API Call**: Component calls service method with `client_op_id`
3. **Server Processing**: Backend processes request and updates authoritative state
4. **Event Broadcasting**: Server broadcasts state changes via WebSocket
5. **Store Updates**: Pinia stores receive and apply state updates
6. **UI Reactivity**: Vue components automatically re-render with new state

## Overview

The frontend for The Open Music Box is built with Vue.js and provides a responsive web interface for:
- Managing music playlists and tracks
- Uploading audio files
- Controlling playback
- Configuring NFC tag associations
- Monitoring system status

## Project Structure

```
front/
├── public/                 # Static assets that are copied without processing
│   ├── img/                # Images and icons
│   ├── favicon.ico         # Website favicon
│   └── index.html          # HTML template
├── scripts/                # Build and optimization scripts
│   ├── optimize-images.js  # Image optimization script
│   └── optimize-logo.js    # Logo optimization script
├── src/                    # Source code
│   ├── assets/             # Assets that will be processed by webpack
│   ├── components/         # Vue components
│   │   ├── ServerAuthoritative/ # Server-state aware components
│   │   ├── audio/          # Audio playback components
│   │   ├── files/          # File management components
│   │   ├── upload/         # File upload components
│   │   └── HeaderNavigation.vue # Main navigation
│   ├── services/           # Service layer for API communication
│   │   ├── realApiService.ts    # HTTP API service implementation
│   │   ├── realSocketService.ts # WebSocket service implementation
│   │   ├── dataService.ts       # Data transformation service
│   │   └── cacheService.ts      # Client-side caching
│   ├── stores/             # Pinia stores for state management
│   │   ├── serverStateStore.ts  # Server state synchronization
│   │   └── uploadStore.ts       # Upload state management
│   ├── types/              # TypeScript type definitions
│   ├── utils/              # Utility functions
│   ├── views/              # Page components
│   ├── router/             # Vue Router configuration
│   ├── i18n/               # Internationalization
│   ├── theme/              # UI theme configuration
│   ├── constants/          # Application constants
│   ├── App.vue             # Root component
│   └── main.ts             # Application entry point
├── .env                    # Environment variables
├── .env.build              # Production build environment variables
├── .env.development        # Development environment variables
├── package.json            # NPM dependencies and scripts
├── tsconfig.json           # TypeScript configuration
└── vue.config.js           # Vue CLI configuration
```

### Key Architecture Components

- **`stores/serverStateStore.ts`**: Central Pinia store that manages server state synchronization
- **`services/realSocketService.ts`**: WebSocket service for real-time event handling
- **`services/realApiService.ts`**: HTTP API service with operation tracking
- **`components/ServerAuthoritative/`**: Components designed for server-state pattern
- **`services/dataService.ts`**: Data transformation and normalization layer

## State Management

The frontend uses Pinia stores to manage state synchronization with the backend's authoritative state.

### Server State Store

The `serverStateStore.ts` is the central hub for all server-synchronized state:

```typescript
// Example: Reactive playlist state
const serverState = useServerStateStore()

// Automatically synchronized with server
const playlists = computed(() => serverState.playlists)
const currentTrack = computed(() => serverState.currentTrack)
const playerState = computed(() => serverState.playerState)
```

### State Update Flow

1. **WebSocket Event Reception**: `realSocketService.ts` receives server events
2. **Store Updates**: Events are processed and applied to Pinia stores
3. **Component Reactivity**: Vue components automatically re-render
4. **UI Synchronization**: All connected clients show identical state

### Event Handling Pattern

```typescript
// WebSocket event handling
socketService.on('state:playlists', (event) => {
  serverStateStore.updatePlaylists(event.data)
})

socketService.on('state:player', (event) => {
  serverStateStore.updatePlayerState(event.data)
})
```

## Development Setup

1. **Prerequisites**:
   - Node.js 14+ and npm 6+
   - Backend server running (see `/back/README.md`)

2. **Installation**:
   ```bash
   # Navigate to the frontend directory
   cd front

   # Install dependencies
   npm install
   ```

3. **Start development server**:
   ```bash
   npm run serve
   ```
   This will:
   - Start a development server with hot-reload
   - Compile and place the output in `../back/app/static/`
   - Open the application in your browser at `http://localhost:8080`

## Build Process

The frontend build process is integrated with the backend:

1. **Development build**:
   ```bash
   npm run serve
   ```
   Outputs to `../back/app/static/` for immediate testing with the backend.

2. **Production build**:
   ```bash
   npm run build
   ```
   Creates optimized production files in `dist/` that are later copied to the appropriate location by deployment scripts.

## Key Components

### Server-Authoritative Components
- **`ServerAuthoritative/`**: Components designed for server-state pattern
  - Automatically sync with backend state
  - No local state mutations
  - Real-time updates via WebSocket events

### Audio Playback
- **`audio/`**: Audio player components
  - Server-synchronized playback state
  - Real-time progress updates
  - Volume control with server state

### File Management
- **`files/`**: File and playlist management
  - Server-state synchronized file lists
  - Real-time file operation updates
  - Drag-and-drop with progress tracking

### Upload System
- **`upload/`**: Chunked file upload components
  - Progress tracking with server coordination
  - Error handling and retry logic
  - Real-time upload status updates

### Navigation
- **`HeaderNavigation.vue`**: Main application navigation
  - Server state-aware navigation
  - Real-time status indicators

## API Integration

The frontend communicates with the backend through a layered service architecture:

### HTTP API Service

```typescript
// realApiService.ts - HTTP operations with client_op_id tracking
class RealApiService {
  async createPlaylist(name: string): Promise<ApiResponse> {
    const clientOpId = generateUUID()
    return this.post('/api/playlists', {
      client_op_id: clientOpId,
      name
    })
  }
}
```

### Service Layer Architecture

- **`realApiService.ts`**: HTTP API implementation with operation tracking
- **`dataService.ts`**: Data transformation and normalization
- **`cacheService.ts`**: Client-side caching for performance
- **`lazyServices.ts`**: Lazy loading of heavy services

### Operation Tracking

All mutations include `client_op_id` for operation correlation:

```typescript
// Client sends operation
const response = await api.createPlaylist('My Playlist')

// Server responds with acknowledgment
if (response.success) {
  // Operation successful, state will be updated via WebSocket
}
```

## WebSocket Integration

Real-time state synchronization is handled through WebSocket events:

### Event Subscription

```typescript
// realSocketService.ts - WebSocket event handling
class RealSocketService {
  connect() {
    this.socket = io(SOCKET_URL)

    // Subscribe to state events
    this.socket.on('state:playlists', this.handlePlaylistsUpdate)
    this.socket.on('state:player', this.handlePlayerUpdate)
    this.socket.on('state:track_progress', this.handleProgressUpdate)
  }

  private handlePlaylistsUpdate(event: StateEvent) {
    // Update store with server state
    serverStateStore.updatePlaylists(event.data)
  }
}
```

### Event Types

The frontend handles these server state events:

- **`state:playlists`**: Complete playlists snapshot
- **`state:playlist`**: Individual playlist updates
- **`state:player`**: Audio player state changes
- **`state:track_progress`**: Real-time playback progress
- **`state:volume_changed`**: System volume updates
- **`state:nfc_state`**: NFC reader status

### Sequence Handling

Events include `server_seq` for proper ordering:

```typescript
interface StateEvent {
  event_type: string
  server_seq: number
  data: any
  timestamp: number
}
```

## Configuration

Environment-specific configuration is managed through `.env` files:

- `.env`: Base configuration shared across all environments
- `.env.development`: Development-specific settings
- `.env.build`: Production build settings

Key configuration options:
```
VUE_APP_API_BASE_URL=http://localhost:5004/api
VUE_APP_SOCKET_URL=http://localhost:5004
VUE_APP_TITLE=The Open Music Box
```

## Development Patterns

### Adding New Features

1. **Define Types**: Add TypeScript interfaces in `types/`
2. **API Service**: Extend `realApiService.ts` with new endpoints
3. **Store Integration**: Update stores to handle new state
4. **WebSocket Events**: Add event handlers for real-time updates
5. **Components**: Create reactive components using server state

### Component Development

```typescript
// Example: Server-state aware component
<template>
  <div>
    <h2>{{ playlist.name }}</h2>
    <track-list :tracks="playlist.tracks" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useServerStateStore } from '@/stores/serverStateStore'

const props = defineProps<{ playlistId: string }>()
const serverState = useServerStateStore()

// Reactive server state
const playlist = computed(() =>
  serverState.getPlaylistById(props.playlistId)
)
</script>
```

### State Management Best Practices

- **Never mutate server state locally**: Always go through API calls
- **Use computed properties**: For reactive derived state
- **Handle loading states**: Show appropriate UI during API operations
- **Error handling**: Gracefully handle API and WebSocket errors

## Testing

Tests are written using Vitest with focus on state management and service integration:

```bash
# Run tests
npm run test

# Run tests with coverage
npm run test:coverage
```

### Testing Patterns

- **Store Testing**: Test Pinia stores with mock WebSocket events
- **Service Testing**: Mock API responses and WebSocket connections
- **Component Testing**: Test reactive behavior with server state changes
- **Integration Testing**: Test complete user workflows with state synchronization

## Deployment

The frontend is automatically deployed as part of the backend deployment process:

1. The frontend is built using `npm run build`
2. Build output is copied to the backend's static directory
3. The backend serves the frontend files

For more details on deployment, see the main project README.md.

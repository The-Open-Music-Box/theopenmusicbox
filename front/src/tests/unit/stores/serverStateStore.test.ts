/**
 * Unit tests for serverStateStore.ts
 *
 * Tests the real-time WebSocket state management store including:
 * - Player state management via readonly getters
 * - Playlist state synchronization
 * - DOM event handling for state updates
 * - Socket service integration
 * - API service integration for initial state
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useServerStateStore } from '@/stores/serverStateStore'

// Mock socketService
vi.mock('@/services/socketService', () => ({
  default: {
    on: vi.fn(),
    off: vi.fn(),
    emit: vi.fn(),
    isConnected: vi.fn(() => true),
    connect: vi.fn(),
    disconnect: vi.fn()
  }))

// Mock apiService for requestInitialPlayerState
vi.mock('@/services/apiService', () => ({
  default: {
    getPlayerStatus: vi.fn()
  }))

// Mock logger
vi.mock('@/utils/logger', () => ({
  logger: {
    info: vi.fn(),
    error: vi.fn(),
    debug: vi.fn(),
    warn: vi.fn()
  }))

// Mock SOCKET_EVENTS constants
vi.mock('@/constants/apiRoutes', () => ({
  SOCKET_EVENTS: {
    ACK_OP: 'ack_op',
    ERR_OP: 'err_op',
    SYNC_REQUEST: 'sync_request'
  }))

describe('serverStateStore', () => {
  let store: ReturnType<typeof useServerStateStore>
  let pinia: ReturnType<typeof createPinia>
  let mockSocketService: any
  let mockApiService: any

  beforeEach(async () => {
    pinia = createPinia()
    setActivePinia(pinia)

    // Get the mocked services
    mockSocketService = (await import('@/services/socketService')).default
    mockApiService = (await import('@/services/apiService')).default

    store = useServerStateStore()
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('Store Initialization', () => {
    it('should initialize with default state', () => {
      expect(store.isConnected).toBe(false)
      expect(store.playerState).toEqual(expect.objectContaining({
        is_playing: false,
        active_playlist_id: null,
        active_track: null,
        position_ms: 0,
        duration_ms: 0,
        track_index: 0,
        track_count: 0,
        can_prev: false,
        can_next: false,
        server_seq: 0
      }))
      expect(store.playlists).toEqual([])
      expect(store.globalSequence).toBe(0)
    })

    it('should have proper reactive state', () => {
      expect(typeof store.playerState.is_playing).toBe('boolean')
      expect(typeof store.playerState).toBe('object')
      expect(Array.isArray(store.playlists)).toBe(true)
      expect(typeof store.isConnected).toBe('boolean')
      expect(typeof store.isReconnecting).toBe('boolean')
    })
  })

  describe('Socket Integration', () => {
    it('should initialize socket service integration', () => {
      // The store integrates with socket service
      // We can't easily test the event handlers setup due to module loading order
      // But we can verify the store has the socket integration methods
      expect(typeof store.subscribeToPlaylists).toBe('function')
      expect(typeof store.subscribeToPlaylist).toBe('function')
      expect(typeof store.unsubscribeFromPlaylist).toBe('function')
      expect(typeof store.requestStateSync).toBe('function')
    })

    it('should subscribe to playlists', () => {
      const result = store.subscribeToPlaylists()
      expect(result).toBe(true)
      expect(mockSocketService.emit).toHaveBeenCalledWith('join:playlists', {})
    })

    it('should subscribe to specific playlist', () => {
      const playlistId = 'playlist-123'
      store.subscribeToPlaylist(playlistId)
      expect(mockSocketService.emit).toHaveBeenCalledWith('join:playlist', { playlist_id: playlistId })
    })

    it('should unsubscribe from specific playlist', () => {
      const playlistId = 'playlist-123'
      store.unsubscribeFromPlaylist(playlistId)
      expect(mockSocketService.emit).toHaveBeenCalledWith('leave:playlist', { playlist_id: playlistId })
    })

    it('should request state sync', () => {
      store.requestStateSync()
      expect(mockSocketService.emit).toHaveBeenCalledWith('sync_request', expect.any(Object))
    })
  })

  describe('DOM Event Handling', () => {
    it('should handle player state DOM events', () => {
      const mockPlayerState = {
        is_playing: true,
        active_playlist_id: 'playlist-1',
        active_track: { id: 'track-1', title: 'Test Track', filename: 'test.mp3' },
        position_ms: 5000,
        duration_ms: 180000,
        track_index: 2,
        track_count: 10,
        can_prev: true,
        can_next: true,
        volume: 75,
        server_seq: 123
      }

      // Simulate DOM event
      const event = new CustomEvent('state:player', { detail: mockPlayerState })
      window.dispatchEvent(event)

      expect(store.playerState.is_playing).toBe(true)
      expect(store.playerState.active_playlist_id).toBe('playlist-1')
      expect(store.playerState.active_track?.title).toBe('Test Track')
      expect(store.playerState.position_ms).toBe(5000)
      expect(store.playerState.volume).toBe(75)
    })

    it('should handle playlists snapshot DOM events', () => {
      const mockPlaylists = [
        { id: 'pl1', title: 'Playlist 1', description: 'First playlist', tracks: [], track_count: 0 },
        { id: 'pl2', title: 'Playlist 2', description: 'Second playlist', tracks: [], track_count: 0 }
      ]

      const event = new CustomEvent('state:playlists', {
        detail: { data: { playlists: mockPlaylists }, server_seq: 100 })
      window.dispatchEvent(event)

      expect(store.playlists).toHaveLength(2)
      expect(store.playlists[0].title).toBe('Playlist 1')
      expect(store.globalSequence).toBe(100)
    })

    it('should handle track position DOM events', () => {
      const positionData = {
        position_ms: 30000,
        duration_ms: 200000,
        is_playing: true,
        track_id: 'track-123'
      }

      const event = new CustomEvent('state:track_position', {
        detail: { data: positionData, server_seq: 105 })
      window.dispatchEvent(event)

      expect(store.playerState.position_ms).toBe(30000)
      expect(store.playerState.duration_ms).toBe(200000)
      expect(store.playerState.is_playing).toBe(true)
      expect(store.globalSequence).toBe(105)
    })

    it('should handle playlist deletion DOM events', () => {
      // First add some playlists
      store.manualSync([
        { id: 'pl1', title: 'Playlist 1', description: 'First', tracks: [], track_count: 0 },
        { id: 'pl2', title: 'Playlist 2', description: 'Second', tracks: [], track_count: 0 }
      ])

      const event = new CustomEvent('state:playlist_deleted', {
        detail: { data: { playlist_id: 'pl1' }, server_seq: 110 })
      window.dispatchEvent(event)

      expect(store.playlists).toHaveLength(1)
      expect(store.playlists[0].id).toBe('pl2')
      expect(store.globalSequence).toBe(110)
    })

    it('should handle volume change DOM events', () => {
      const event = new CustomEvent('state:volume_changed', {
        detail: { data: { volume: 85 }, server_seq: 115 })
      window.dispatchEvent(event)

      expect(store.playerState.volume).toBe(85)
      expect(store.globalSequence).toBe(115)
    })
  })

  describe('Getters and Computed Properties', () => {
    it('should get playlist by ID', () => {
      const playlists = [
        { id: 'pl1', title: 'Playlist 1', description: 'First', tracks: [], track_count: 0 },
        { id: 'pl2', title: 'Playlist 2', description: 'Second', tracks: [], track_count: 0 }
      ]
      store.manualSync(playlists)

      const found = store.getPlaylistById('pl2')
      expect(found?.title).toBe('Playlist 2')

      const notFound = store.getPlaylistById('nonexistent')
      expect(notFound).toBeUndefined()
    })

    it('should get playlist sequence', () => {
      const seq = store.getPlaylistSequence('test-playlist')
      expect(seq).toBe(0) // Default value
    })
  })

  describe('API Integration', () => {
    it('should request initial player state', async () => {
      const mockPlayerStatus = {
        is_playing: true,
        active_playlist_id: 'pl1',
        active_track: { id: 't1', title: 'Track 1', filename: 'track1.mp3' },
        position_ms: 10000,
        duration_ms: 180000,
        server_seq: 50
      }

      mockApiService.getPlayerStatus.mockResolvedValue(mockPlayerStatus)

      await store.requestInitialPlayerState()

      expect(mockApiService.getPlayerStatus).toHaveBeenCalled()
      expect(store.playerState.is_playing).toBe(true)
      expect(store.playerState.active_playlist_id).toBe('pl1')
    })

    it('should handle API errors gracefully', async () => {
      mockApiService.getPlayerStatus.mockRejectedValue(new Error('API Error'))

      await expect(store.requestInitialPlayerState()).resolves.not.toThrow()
    })
  })

  describe('Manual Sync', () => {
    it('should manually sync playlists', () => {
      const testPlaylists = [
        { id: 'manual1', title: 'Manual 1', description: 'Test', tracks: [], track_count: 0 },
        { id: 'manual2', title: 'Manual 2', description: 'Test', tracks: [], track_count: 0 }
      ]

      store.manualSync(testPlaylists)

      expect(store.playlists).toHaveLength(2)
      expect(store.playlists[0].title).toBe('Manual 1')
      expect(store.playlists[1].title).toBe('Manual 2')
    })
  })

  describe('Readonly Properties', () => {
    it('should expose readonly state properties', () => {
      // These properties should be readonly and the operations should be silently ignored
      // Instead of throwing, Vue's readonly wrapper just warns and prevents the operation

      const originalPlaylistsLength = store.playlists.length
      const originalIsPlaying = store.playerState.is_playing
      const originalIsConnected = store.isConnected

      // Try to modify readonly properties (should be silently ignored)
      try {
        // @ts-expect-error - Testing readonly behavior
        store.playlists.push({ id: 'test', title: 'test', description: 'test', tracks: [], track_count: 0 })
      } catch (e) {
        // Expected in readonly mode
      }

      try {
        // @ts-expect-error - Testing readonly behavior
        store.playerState.is_playing = true
      } catch (e) {
        // Expected in readonly mode
      }

      try {
        // @ts-expect-error - Testing readonly behavior
        store.isConnected = true
      } catch (e) {
        // Expected in readonly mode
      }

      // Verify values haven't changed
      expect(store.playlists.length).toBe(originalPlaylistsLength)
      expect(store.playerState.is_playing).toBe(originalIsPlaying)
      expect(store.isConnected).toBe(originalIsConnected)
    })
  })

  describe('Socket Connection State', () => {
    it('should handle connection state through socket service', () => {
      // The actual store doesn't expose direct connection methods
      // Connection is handled through socketService
      expect(store.isConnected).toBe(false)
      expect(store.isReconnecting).toBe(false)
    })
  })
})
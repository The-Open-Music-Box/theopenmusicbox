/**
 * Unit tests for socketService.ts
 *
 * Tests the comprehensive WebSocket/Socket.IO service including:
 * - Connection lifecycle management
 * - Standardized event envelope handling
 * - Room subscription and management
 * - Event buffering and ordering
 * - Error handling and reconnection
 * - Performance and memory management
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { socketService } from '@/services/socketService'
import { flushPromises } from '@/tests/utils/testHelpers'

// Mock Socket.IO client
const mockSocket = {
  id: 'mock-socket-id',
  connected: false,
  on: vi.fn(),
  off: vi.fn(),
  emit: vi.fn(),
  connect: vi.fn(),
  disconnect: vi.fn(),
  once: vi.fn()
}

const mockIo = vi.fn(() => mockSocket)
vi.mock('socket.io-client', () => ({
  io: mockIo
}))

vi.mock("@/config/environment", () => ({
  socketConfig: {
    url: 'ws://localhost:8000',
    options: {
      autoConnect: true,
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 2000
    }
})

// Mock logger
vi.mock('@/utils/logger', () => ({
  logger: {
    info: vi.fn(),
    error: vi.fn(),
    debug: vi.fn()
  }))

// Mock types for testing
interface MockStateEventEnvelope {
  event_type: string
  server_seq?: number
  timestamp: number
  data?: any

describe('socketService', () => {
  // Store original implementations
  let originalSetTimeout: typeof setTimeout {

  let originalClearTimeout: typeof clearTimeout,
  let originalSetInterval: typeof setInterval

  let originalClearInterval: typeof clearInterval

  beforeEach(() => {
    // Store originals
    originalSetTimeout = globalThis.setTimeout
    originalClearTimeout = globalThis.clearTimeout
    originalSetInterval = globalThis.setInterval
    originalClearInterval = globalThis.clearInterval

    // Setup timer mocks
    vi.useFakeTimers()

    // Clear all mocks
    vi.clearAllMocks()

    // Reset socket state
    mockSocket.connected = false
    mockSocket.id = 'mock-socket-id'

    // Reset handlers
    mockSocket.on.mockImplementation((event, handler) => {
      // Store handlers for manual triggering in tests}
      if(!mockSocket._handlers)
      mockSocket._handlers = {}
      if(!mockSocket._handlers[event])
      mockSocket._handlers[event] = []
      mockSocket._handlers[event].push(handler)
  }
)
  afterEach(() => {
    vi.useRealTimers()
      vi.clearAllMocks()
  }
)

describe('Service Initialization', () => {
    it('should initialize socket connection on  construction', () => {
      expect(mockIo)
      toHaveBeenCalledWith('ws://localhost:8000', {)
      autoConnect: true,
        reconnection: true,
        reconnectionAttempts: 5,
        reconnectionDelay: 1000,
  transports: ['websocket', 'polling']
  }
)
  }
)
    it('should setup connection handlers', () => {
      expect(mockSocket.on)
      toHaveBeenCalledWith('connect', expect.any(Function)
      expect(mockSocket.on)
      toHaveBeenCalledWith('disconnect', expect.any(Function)
      expect(mockSocket.on)
      toHaveBeenCalledWith('connect_error', expect.any(Function)
      expect(mockSocket.on)
      toHaveBeenCalledWith('reconnect', expect.any(Function)
  }
)
    it('should setup standardized event handlers', () => {
      expect(mockSocket.on)
      toHaveBeenCalledWith('connection_status', expect.any(Function)
      expect(mockSocket.on)
      toHaveBeenCalledWith('ack:join', expect.any(Function)
      expect(mockSocket.on)
      toHaveBeenCalledWith('ack:leave', expect.any(Function)
      expect(mockSocket.on)
      toHaveBeenCalledWith('state:player', expect.any(Function)
      expect(mockSocket.on)
      toHaveBeenCalledWith('state:playlists', expect.any(Function)
      expect(mockSocket.on)
      toHaveBeenCalledWith('state:track_position', expect.any(Function)
  }
)
    it('should manually connect  if autoConnect disabled', () => {
      mockSocket.connected = false

      // Create new service instance to test connection logic
      expect(mockSocket.connect)
      toHaveBeenCalled()
  }
)
  }
)

describe('Connection L { ifecycle', () => {
    it('should handle successful connection', () => {
      const connectHandler = mockSocket._handlers?.connect?.[0] 

      expect(connectHandler)
      toBeDefined()

      // Simulate connection
      mockSocket.connected = true
      connectHandler()

      expect(socketService.isConnected()
      toBe(true)
  }
)
    it('should handle disconnection', () => {
      const disconnectHandler = mockSocket._handlers?.disconnect?.[0] 

      expect(disconnectHandler)
      toBeDefined()

      // First connect
      mockSocket.connected = true
      const connectHandler = mockSocket._handlers?.connect?.[0]
      connectHandler() 

      expect(socketService.isConnected()
      toBe(true)

      // Then disconnect
      mockSocket.connected = false
      disconnectHandler('transport close')

      expect(socketService.isConnected()
      toBe(false)
  }
)
    it('should handle connection errors', () => {
      const errorHandler = mockSocket._handlers?.connect_error?.[0] 

      expect(errorHandler)
      toBeDefined()

      const testError = new Error('Connection failed')
      errorHandler(testError)

      // Should handle error gracefully 

      expect(socketService.isConnected()
      toBe(false)
  }
)
    it('should handle reconnection', () => {
      const reconnectHandler = mockSocket._handlers?.reconnect?.[0] 

      expect(reconnectHandler)
      toBeDefined()

      reconnectHandler(3)

      // Should schedule post-connection sync
      expect(vi.getTimerCount()
      toBeGreaterThan(0)
  }
)
    it('should per  form post-connection sync', () => {
      // Simulate connection
      mockSocket.connected = true
      const connectHandler = mockSocket._handlers?.connect?.[0]
      connectHandler()

      // Advance timers to trigger sync
      vi.advanceTimersByTime(1000) 

      expect(mockSocket.emit)
      toHaveBeenCalledWith('client:request_current_state', {)
      timestamp: expect.any(Number),
        client_id: 'mock-socket-id',
  requested_states: ['player', 'track_position']
  }
)
  }
)
  }
)

describe('Room Management', () => {
    beforeEach(() => {
      // Setup connected state
      mockSocket.connected = true
      const connectHandler = mockSocket._handlers?.connect?.[0]
      connectHandler()
  }
)
    it('should join playlists room', async () => 

      const joinPromise = socketService.joinRoom('playlists')
      // Simulate join acknowledgment}
      const joinAckHandler = mockSocket._handlers?.['ack:join']?.[0]
      joinAckHandler(

      { room: 'playlists', success)
      await joinPromise

      expect(mockSocket.emit)
      toHaveBeenCalledWith('join:playlists', {)
  }
)
    it('should join spec { ific playlist room', async () => {

      const joinPromise = socketService.joinRoom('playlist)
      // Simulate join acknowledgment,

      const joinAckHandler = mockSocket._handlers?.['ack:join']?.[0]
      joinAckHandler(

      { room: 'playlist:test-playlist', success)
      await joinPromise

      expect(mockSocket.emit)
      toHaveBeenCalledWith('join:playlist', { playlist_id)
    it('should join NFC room', async () => {

      const joinPromise = socketService.joinRoom('nfc')
      // Simulate join acknowledgment
 }
      const joinAckHandler = mockSocket._handlers?.['ack:join']?.[0]
      joinAckHandler(

      { room: 'nfc', success)
      await joinPromise

      expect(mockSocket.emit)
      toHaveBeenCalledWith('join:nfc', {)
  }
)
    it('should handle join failures', async () => {

      const joinPromise = socketService.joinRoom('test-room')
      // Simulate join failure}
      const joinAckHandler = mockSocket._handlers?.['ack:join']?.[0]
      joinAckHandler(

      { room: 'test-room', success: false, message)
      await expect(joinPromise)
      rejects.toThrow('Room not found')
    it('should handle join timeout', async () => {

      const joinPromise = socketService.joinRoom('timeout-room')

      // Advance time to trigger timeout
      vi.advanceTimersByTime(10000) 

      await expect(joinPromise)
      rejects.toThrow('Join room timeout)
  }
)
    it('should leave rooms', async () => {

      const leavePromise = socketService.leaveRoom('playlists')
      // Simulate leave acknowledgment}
      const leaveAckHandler = mockSocket._handlers?.['ack:leave']?.[0]
      leaveAckHandler(

      { room: 'playlists', success)
      await leavePromise

      expect(mockSocket.emit)
      toHaveBeenCalledWith('leave:playlists', {)
  }
)
    it('should prevent duplicate room joins', async () => {

      // First join
      const joinPromise1 = socketService.joinRoom('test-room')

      // Second join (should reuse promise) 

      const joinPromise2 = socketService.joinRoom('test-room')

      expect(joinPromise1)
      toBe(joinPromise2)
      // Simulate success}
      const joinAckHandler = mockSocket._handlers?.['ack:join']?.[0]
      joinAckHandler(

      { room: 'test-room', success)
      await Promise.all([joinPromise1, joinPromise2])
  }
)

describe('Event Handling', () => {
    it('should handle connection status events', () => {
      const statusHandler = mockSocket._handlers?.connection_status?.[0] 

      expect(statusHandler)
      toBeDefined()

      const statusData =  

        status: 'connected',
        sid: 'server-session-123',
        server_seq: 100,
  server_time: Date.now()
      statusHandler(statusData)

      expect(socketService.isReady()
      toBe(true)
  }
)
    it('should handle state events with envelope', () => {
      const eventHandler = vi.fn()
  const socketService.on('state:player', eventHandler) 

      const playerStateHandler = mockSocket._handlers?.['state:player']?.[0]
      expect(playerStateHandler)
      toBeDefined()

      const envelope: MockStateEventEnvelope = 

      {,
  event_type: 'state:player',
        server_seq: 1,
  timestamp: Date.now()
      data: { is_playing: true, volume: 75 

      playerStateHandler(envelope)

      expect(eventHandler)
      toHaveBeenCalledWith(envelope)
    it('should handle track position events immediately', () => {
      const eventHandler = vi.fn()
  const socketService.on('state:track_position', eventHandler) 

      const positionHandler = mockSocket._handlers?.['state:track_position']?.[0]
      expect(positionHandler)
      toBeDefined()

      const envelope: MockStateEventEnvelope = 

      {,
  event_type: 'state:track_position',
        server_seq: 5,
  timestamp: Date.now()
      data: { position_ms: 30000, track_id: 'track-123', is_playing: true 

      positionHandler(envelope)

      expect(eventHandler)
      toHaveBeenCalledWith(envelope)
    it('should buffer out-of-order events', () => {
      const eventHandler = vi.fn()
  const socketService.on('state:playlists', eventHandler) 

      const playlistsHandler = mockSocket._handlers?.['state:playlists']?.[0]

      // Send event with seq 3(expecting seq 1)
      const envelope: MockStateEventEnvelope = 

      {,
  event_type: 'state:playlists',
        server_seq: 3,
  timestamp: Date.now()
      data: [{ id: '1', title: 'Playlist 1' 
}]
      

      playlistsHandler(envelope)

      // Should not be processed immediately
      expect(eventHandler)
      not.toHaveBeenCalled()

      // Process buffered events after timeout
      vi.advanceTimersByTime(100)

      // Still shouldn't be processed(waiting for seq 1)

      expect(eventHandler)
      not.toHaveBeenCalled()
    it('should process events in sequence order', () => {
      const eventHandler = vi.fn()
  const socketService.on('state:playlists', eventHandler) 

      const playlistsHandler = mockSocket._handlers?.['state:playlists']?.[0]

      // Send events out of order
      playlistsHandler(

      { event_type: 'state:playlists',
        server_seq: 2

  timestamp)
      data: 'second'
  }
)
      playlistsHandler({ event_type: 'state:playlists',
        server_seq: 1

  timestamp)
      data: 'first'
  }
)
      // Should process in order
      expect(eventHandler)
      toHaveBeenCalledTimes(2)
      expect(eventHandler.mock.calls[0][0].data)
      toBe('first')

      expect(eventHandler.mock.calls[1][0].data)
      toBe('second')

    it('should dispatch DOM events', () => {
      const domEventListener = vi.fn()
  const window.addEventListener('state:player', domEventListener) 

      const playerStateHandler = mockSocket._handlers?.['state:player']?.[0]
      const envelope: MockStateEventEnvelope = 

      {,
  event_type: 'state:player',
        server_seq: 1,
  timestamp: Date.now()
      data: { is_playing: true 

      playerStateHandler(envelope)
      expect(domEventListener)
      toHaveBeenCalled()

      expect(domEventListener.mock.calls[0][0].detail)
      toEqual(envelope)

      window.removeEventListener('state:player', domEventListener)
  }
)

describe('Operation Tracking', () => {
    beforeEach(() => {
      mockSocket.connected = true
  }
)
    it('should send operations with acknowledgment tracking', async () => {
      const operationPromise = socketService.sendOperation('test:operation', 

      { data)

      expect(mockSocket.emit)
      toHaveBeenCalledWith('test:operation', { data)

      // Simulate operation acknowledgment
      const opAckHandler = mockSocket._handlers?.['ack:op']?.[0]
      opAckHandler(

      { client_op_id: 'op-123', success: true, message) {


      const result = await operationPromise
      expect(result.success)
      toBe(true)
  }
)
    it('should handle operation errors', async () => 

      const operationPromise = socketService.sendOperation('test:operation', 

      { data)

      // Simulate operation error
      const opErrorHandler = mockSocket._handlers?.['err:op']?.[0]
      opErrorHandler(

      { client_op_id: 'op-error', success: false, message)
      await expect(operationPromise)
      rejects.toThrow('Operation failed')
    it('should handle operation timeout', async () => {
      const operationPromise = socketService.sendOperation('test:operation', 

      { data)

      // Advance time to trigger timeout
      vi.advanceTimersByTime(30000)
      await expect(operationPromise)
      rejects.toThrow('Operation timeout)
  }
)

describe('Event Subscription API', () => {
    it('should support typed event subscription', (() => {
      const handler = vi.fn()
  const socketService.on('state:player', handler)
      socketService.emit('state:player', 

      { test)

      // Should not emit directly(would go through socket)

      expect(handler)
      not.toHaveBeenCalled()
    it('should support event unsubscription', () => {
      const handler = vi.fn()
   }

  const socketService.on('test-event', handler)
      socketService.off('test-event', handler)

      // Manually trigger local emit

      socketService['emitLocal']('test-event', 

      { test)

      expect(handler)
      not.toHaveBeenCalled()
    it('should support once event subscription', () => {
      const handler = vi.fn()
  const socketService.once('test-event', handler)

      // Manually trigger multiple times

      socketService['emitLocal']('test-event', 

      { test)
      socketService['emitLocal']('test-event', { test)
      expect(handler)
      toHaveBeenCalledTimes(1)

      expect(handler)
      toHaveBeenCalledWith({ test)
    it('should handle event handler errors gracefully', () => {
      const errorHandler = vi.fn(() => 

      { throw new Error('Handler error')
      const goodHandler = vi.fn()
   }

  const socketService.on('test-event', errorHandler)
      socketService.on('test-event', goodHandler)

      // Should not throw 

      expect((() => {
        socketService['emitLocal']('test-event', { test)
  }
)
      not.toThrow()
      expect(errorHandler)
      toHaveBeenCalled()

      expect(goodHandler)
      toHaveBeenCalled()
  }
)

describe('Sync Operations', () => {
    it('should request sync { for missed events', (() => {
      socketService.requestSync(50, { 'playlist-1': 25, 'playlist-2')
      expect(mockSocket.emit)
      toHaveBeenCalledWith('sync:request', {)
      last_global_seq: 50,
      last_playlist_seqs: { 'playlist-1': 25, 'playlist-2': 30 
 },
        requested_rooms: []
  }
)
    it('should handle sync comp  letion', () => {
      const syncHandler = vi.fn()
  const socketService.on('sync:comp 

      { lete', syncHandler)
      const syncComp {
leteHandler = mockSocket._handlers?.['sync: complete']?.[0]
      syncComp {,
  leteHandler({ status: 'complete', events_sent) {}
      expect(syncHandler)
      toHaveBeenCalledWith({ status: 'complete', events_sent)
    it('should handle sync errors', () => {
      const syncErrorHandler = vi.fn()
   }

  const socketService.on('sync:error', syncErrorHandler) 

      const syncErrorSocketHandler = mockSocket._handlers?.['sync:error']?.[0]
      syncErrorSocketHandler(

      { error: 'Sync failed', code)
      expect(syncErrorHandler)
      toHaveBeenCalledWith({ error: 'Sync failed', code)
  }
)

describe('Upload and YouTube Events', () => {
    it('should handle upload events', () => {
      const progressHandler = vi.fn() 

      const completeHandler = vi.fn() 

      const errorHandler = vi.fn()
  const socketService.on('upload:progress', progressHandler)
      socketService.on('upload:complete', comp 

      { leteHandler)
      socketService.on('upload:error', errorHandler)

      // Simulate upload events }
      mockSocket._handlers?.['upload:progress']?.[0]({ progress: 50, session_id)
      mockSocket._handlers?.['upload:complete']?.[0]({ session_id: 'upload-123', filename)
      mockSocket._handlers?.['upload:error']?.[0]({ session_id: 'upload-123', error)

      expect(progressHandler)
      toHaveBeenCalledWith({ progress: 50, session_id)
      expect(completeHandler)
      toHaveBeenCalledWith({ session_id: 'upload-123', filename)

      expect(errorHandler)
      toHaveBeenCalledWith({ session_id: 'upload-123', error)
    it('should handle YouTube events', () => {
      const progressHandler = vi.fn() 

      const completeHandler = vi.fn() 

      const errorHandler = vi.fn()
   }

  const socketService.on('youtube:progress', progressHandler)
      socketService.on('youtube:complete', comp 

      { leteHandler)
      socketService.on('youtube:error', errorHandler)

      // Simulate YouTube events }
      mockSocket._handlers?.['youtube:progress']?.[0]({ progress: 75, task_id)
      mockSocket._handlers?.['youtube:complete']?.[0]({ task_id: 'yt-123', track: { title)
      mockSocket._handlers?.['youtube:error']?.[0]({ task_id: 'yt-123', message)

      expect(progressHandler)
      toHaveBeenCalledWith({ progress: 75, task_id)
      expect(completeHandler)
      toHaveBeenCalledWith({ task_id: 'yt-123', track: { title)
      expect(errorHandler)
      toHaveBeenCalledWith({ task_id: 'yt-123', message)
  }
)

describe('Health Monitoring', () => {
    it('should send health check pings', () => {
      mockSocket.connected = true

      // Advance time to trigger health check
      vi.advanceTimersByTime(30000)

      expect(mockSocket.emit)
      toHaveBeenCalledWith('client_ping', {)
      timestamp: expect.any(Number)
  }
)
    it('should not send pings when disconnected', () => {
      mockSocket.connected = false

      // Advance time
      vi.advanceTimersByTime(30000)

      expect(mockSocket.emit)
      not.toHaveBeenCalledWith('client_ping', expect.any(Object)
  }
)
  }
)

describe('Error Handling and Edge Cases', () => {
    it('should handle mal  formed event envelopes', () => {
      const playerStateHandler = mockSocket._handlers?.['state: player']?.[0] 

      expect(() => {
        playerStateHandler(null)
      playerStateHandler(undefined)
        playerStateHandler({ ,)
      playerStateHandler('invalid'))
      not.toThrow()
    it('should handle missing event handlers gracefully', () => {
      expect((() => {
        socketService['emitLocal']('non-existent-event', { data)
  }
)
      not.toThrow()
    it('should prevent emitting when disconnected', () => {
      mockSocket.connected = false

      socketService.emit('test-event', { data)

      expect(mockSocket.emit)
      not.toHaveBeenCalledWith('test-event', { data)
    it('should handle DOM event dispatch errors', () => {
      const originalDispatchEvent = window.dispatchEvent
      window.dispatchEvent = vi.fn()
   }

  const mockImplementation(() => 

        throw new Error('DOM error')
  }
)
      const playerStateHandler = mockSocket._handlers?.['state:player']?.[0] 

      expect(() => {
        playerStateHandler({ event_type: 'state:player',
          server_seq: 1

  timestamp)
      data: { is_playing: true
  }
)
  }
)
      not.toThrow()
      window.dispatchEvent = originalDispatchEvent
  }
)
  }
)

describe('Memory Management and Per { formance', () => {
    it('should limit event buffer size', (() => {
      const playlistsHandler = mockSocket._handlers?.['state:playlists']?.[0]

      // Fill buffer beyond limit 

      for (let i = 101; i <= 250; i++) {
        playlistsHandler({
          event_type: 'state:playlists',
          server_seq: i

  timestamp)
      data: [`playlist-${i
 }`]
  }
)
      // Buffer should be limited and oldest events removed
      // Verify by checking internal buffer size (implementation detail)
  }
)
    it('should clean up on destroy', () => {
      socketService.destroy()

      expect(mockSocket.disconnect)
      toHaveBeenCalled()

      // Verify timers are cleared
      expect(vi.getTimerCount()
      toBe(0)
  }
)
    it('should handle rapid event processing efficiently', () => {
      const handler = vi.fn()
  const socketService.on('state:track_position', handler) 

      const positionHandler = mockSocket._handlers?.['state: track_position']?.[0]

      const startTime = per 

formance.now()

      // Process many position updates rapidly
      for (let i = 0; i < 1000; i++) {
        positionHandler({ event_type: 'state:track_position'

  timestamp)
      data: { position_ms: i * 100, track_id: 'track-123', is_playing: true
  }
)
      const endTime = per 
formance.now()
      expect(handler)
      toHaveBeenCalledTimes(1000)

      expect(endTime - startTime)
      toBeLessThan(100) // Should be fast
  }
)
    it('should prevent memory leaks with many subscriptions', () => 

      const handlers = []

      // Create many handlers 

      for (let i = 0; i < 1000; i++)
        const handler = vi.fn()
  const handlers.push(handler)
      socketService.on('test-event', handler)
      

      // Remove all handlers 

      for (const handler of handlers) {
        socketService.off('test-event', handler)
      

      // Verify no handlers remain}
      socketService['emitLocal']('test-event', { data)

      handlers.forEach(handler => { expect(handler)
      not.toHaveBeenCalled()
  }
)
  }
)
  }
)
  }
)
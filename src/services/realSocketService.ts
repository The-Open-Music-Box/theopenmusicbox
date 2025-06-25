import { io, Socket } from 'socket.io-client'
import { SOCKET_EVENTS } from '../constants/apiRoutes'

/**
 * Real Socket Service
 * Provides a production-ready socket.io implementation for real-time communication with the server.
 * Handles connection management, event emission, and subscription to server events.
 * 
 * This service uses standardized event names from SOCKET_EVENTS constants to ensure
 * consistency with backend socket events.
 */
class RealSocketService {
  private socket: Socket
  private connectionReady = false // Track connection state
  private eventBuffer: Array<{event: string, data: any, callback: (data: any) => void}> = [] // Buffer for early events

  /**
   * Creates a new RealSocketService instance
   * Initializes the socket connection with the configured server URL and connection options
   */
  constructor() {
    const serverUrl = process.env.VUE_APP_API_URL;
    const socketUrl = serverUrl ?? '';
    if (!socketUrl) {
      throw new Error('VUE_APP_API_URL is not defined: cannot connect to socket server');
    }
    console.log('Connecting to socket server at:', socketUrl);

    this.socket = io(socketUrl, {
      transports: ['polling', 'websocket'],
      autoConnect: false,
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5,
      withCredentials: false
    })

    this.setupBaseHandlers()
    console.log('[SocketService] Base handlers registered at', Date.now())
  }

  /**
   * Sets up base event handlers for monitoring socket connection state
   * Registers listeners for connect, disconnect, error, and reconnection events
   * @private
   */
  private setupBaseHandlers() {
    this.socket.on(SOCKET_EVENTS.CONNECT, () => {
      this.connectionReady = true
      console.log('Socket connected successfully', this.socket.id, 'at', Date.now())
      // Process buffered events
      if (this.eventBuffer.length > 0) {
        console.log('[SocketService] Processing', this.eventBuffer.length, 'buffered events at', Date.now())
        this.eventBuffer.forEach(({event, data, callback}) => {
          console.log('[SocketService] Processing buffered event:', event, data, 'at', Date.now())
          callback(data)
        })
        this.eventBuffer = []
      }
    })

    this.socket.on(SOCKET_EVENTS.CONNECT_ERROR, (error) => {
      console.error('Connection error:', error)
    })

    this.socket.on(SOCKET_EVENTS.DISCONNECT, (reason) => {
      this.connectionReady = false
      console.log('Socket disconnected:', reason, 'at', Date.now())
    })

    this.socket.on(SOCKET_EVENTS.RECONNECT, (attemptNumber) => {
      console.log('Socket reconnected after', attemptNumber, 'attempts')
    })

    this.socket.on(SOCKET_EVENTS.ERROR, (error) => {
      console.error('Socket error:', error)
    })
    
    // Set up listeners for playback events
    this.setupPlaybackHandlers()
    
    // Set up listeners for NFC events
    this.setupNfcHandlers()
    
    // Set up listeners for upload events
    this.setupUploadHandlers()
    
    // Set up listeners for system events
    this.setupSystemHandlers()
  }
  
  /**
   * Sets up handlers for playback-related socket events
   * @private
   */
  private setupPlaybackHandlers() {
    const playbackEvents = [
      SOCKET_EVENTS.PLAYBACK_STARTED,
      SOCKET_EVENTS.PLAYBACK_STOPPED,
      SOCKET_EVENTS.PLAYBACK_PAUSED,
      SOCKET_EVENTS.PLAYBACK_RESUMED,
      SOCKET_EVENTS.TRACK_CHANGED,
      SOCKET_EVENTS.PLAYBACK_PROGRESS,
      SOCKET_EVENTS.PLAYBACK_ERROR
    ]
    
    playbackEvents.forEach(event => {
      this.socket.on(event, (data) => {
        console.log(`[SocketService] Received ${event} event:`, data)
      })
    })
  }
  
  /**
   * Sets up handlers for NFC-related socket events
   * @private
   */
  private setupNfcHandlers() {
    const nfcEvents = [
      SOCKET_EVENTS.NFC_TAG_DETECTED,
      SOCKET_EVENTS.NFC_ASSOCIATION_COMPLETE,
      SOCKET_EVENTS.NFC_ERROR
    ]
    
    nfcEvents.forEach(event => {
      this.socket.on(event, (data) => {
        console.log(`[SocketService] Received ${event} event:`, data)
      })
    })
  }
  
  /**
   * Sets up handlers for upload-related socket events
   * @private
   */
  private setupUploadHandlers() {
    const uploadEvents = [
      SOCKET_EVENTS.UPLOAD_PROGRESS,
      SOCKET_EVENTS.UPLOAD_COMPLETE,
      SOCKET_EVENTS.UPLOAD_ERROR
    ]
    
    uploadEvents.forEach(event => {
      this.socket.on(event, (data) => {
        console.log(`[SocketService] Received ${event} event:`, data)
      })
    })
  }
  
  /**
   * Sets up handlers for system-related socket events
   * @private
   */
  private setupSystemHandlers() {
    const systemEvents = [
      SOCKET_EVENTS.VOLUME_CHANGED,
      SOCKET_EVENTS.SYSTEM_HEALTH
    ]
    
    systemEvents.forEach(event => {
      this.socket.on(event, (data) => {
        console.log(`[SocketService] Received ${event} event:`, data)
      })
    })
  }

  /**
   * Initiates the socket connection if not already connected
   */
  setupSocketConnection() {
    console.log('[SocketService] setupSocketConnection called at', Date.now())
    if (!this.socket.connected) {
      console.log('[SocketService] Calling .connect() at', Date.now())
      this.socket.connect()
    } else {
      console.log('[SocketService] Socket already connected at', Date.now())
    }
  }

  /**
   * Sends an event to the server
   * @param event - Name of the event to emit
   * @param data - Data payload to send with the event
   */
  emit(event: string, data: any) {
    if (!this.connectionReady) {
      console.warn('[SocketService] Attempting to emit while socket is not fully connected:', event, 'at', Date.now())
      return
    }
    console.log('[SocketService] Emitting event:', event, data, 'at', Date.now());
    this.socket.emit(event, data)
  }

  /**
   * Registers an event listener for socket events
   * @param event - Name of the event to listen for
   * @param callback - Function to call when the event occurs
   */
  on(event: string, callback: (data: any) => void) {
    console.log('[SocketService] Registering handler for event:', event, 'at', Date.now())
    this.socket.on(event, (data: any) => {
      if (!this.connectionReady && event !== SOCKET_EVENTS.CONNECT) {
        // Buffer the event for processing after connect
        console.warn('[SocketService] Buffering event before connect:', event, data, 'at', Date.now())
        this.eventBuffer.push({event, data, callback})
        return
      }
      console.log('[SocketService] Received event:', event, data, 'at', Date.now());
      callback(data);
    })
  }

  /**
   * Removes an event listener for the specified event
   * @param event - Name of the event to stop listening for
   */
  off(event: string) {
    this.socket.off(event)
  }

  /**
   * Disconnects from the socket server if connected
   */
  disconnect() {
    if (this.socket.connected) {
      this.socket.disconnect()
    }
  }

  /**
   * Checks if the socket is currently connected
   * @returns True if connected, false otherwise
   */
  isConnected(): boolean {
    return this.socket.connected
  }

  /**
   * Gets the current socket ID if connected
   * @returns Socket ID string or null if not connected
   */
  getSocketId(): string | null {
    return this.socket.id || null;
  }

  /**
   * Forces a reconnection by disconnecting and then connecting again
   * Useful for resetting the connection state
   */
  reconnect() {
    this.socket.disconnect().connect()
  }
}

export default new RealSocketService()
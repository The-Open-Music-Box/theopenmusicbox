import { io, Socket } from 'socket.io-client'

/**
 * Real Socket Service
 * Provides a production-ready socket.io implementation for real-time communication with the server.
 * Handles connection management, event emission, and subscription to server events.
 */
class RealSocketService {
  private socket: Socket

  /**
   * Creates a new RealSocketService instance
   * Initializes the socket connection with the configured server URL and connection options
   */
  constructor() {
    const serverUrl = process.env.VUE_APP_API_URL;
    const serverPort = process.env.VUE_APP_SRVE_PORT;

    const socketUrl = `${serverUrl}:${serverPort}`;
    console.log('Connecting to socket server at:', socketUrl);

    this.socket = io(socketUrl, {
      transports: ['websocket'],
      autoConnect: false,
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5
    })

    this.setupBaseHandlers()
  }

  /**
   * Sets up base event handlers for monitoring socket connection state
   * Registers listeners for connect, disconnect, error, and reconnection events
   * @private
   */
  private setupBaseHandlers() {
    this.socket.on('connect', () => {
      console.log('Socket connected successfully', this.socket.id)
    })

    this.socket.on('connect_error', (error) => {
      console.error('Connection error:', error)
    })

    this.socket.on('disconnect', (reason) => {
      console.log('Socket disconnected:', reason)
    })

    this.socket.on('reconnect', (attemptNumber) => {
      console.log('Socket reconnected after', attemptNumber, 'attempts')
    })

    this.socket.on('error', (error) => {
      console.error('Socket error:', error)
    })
  }

  /**
   * Initiates the socket connection if not already connected
   */
  setupSocketConnection() {
    if (!this.socket.connected) {
      this.socket.connect()
    }
  }

  /**
   * Sends an event to the server
   * @param event - Name of the event to emit
   * @param data - Data payload to send with the event
   */
  emit(event: string, data: any) {
    if (!this.socket.connected) {
      console.warn('Attempting to emit while socket is not connected:', event)
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
    this.socket.on(event, (data: any) => {
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
import { io, Socket } from 'socket.io-client'
import { SOCKET_EVENTS } from '../constants/apiRoutes'
import { logger } from '../utils/logger'
import type { SocketEventHandler } from '../types/socket'

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
  private eventBuffer: Array<{event: string, data: unknown, callback: SocketEventHandler}> = [] // Buffer for early events

  /**
   * Creates a new RealSocketService instance
   * Initializes the socket connection with the configured server URL and connection options
   */
  constructor() {
    // Use API URL from environment variables
    // This ensures connection to the correct socket server regardless of how the frontend is accessed
    const socketUrl = `${window.location.origin}`;

    this.socket = io(socketUrl, {
      transports: ['polling', 'websocket'],
      autoConnect: false,
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5,
      withCredentials: false
    });

    this.setupSocketHandlers();
  }

  /**
   * Sets up base event handlers for monitoring socket connection state
   * Registers listeners for connect, disconnect, error, and reconnection events
   * @private
   */
  private setupSocketHandlers(): void {
    this.socket.on(SOCKET_EVENTS.CONNECT, () => {
      logger.debug('Socket connected successfully', {}, 'RealSocketService');
      this.connectionReady = true;

      // Process buffered events
      if (this.eventBuffer.length > 0) {
        logger.debug(`Processing ${this.eventBuffer.length} buffered events`, {}, 'RealSocketService');
        this.eventBuffer.forEach(({data, callback}) => {
          callback(data);
        });
        this.eventBuffer = [];
      }
    });

    this.socket.on(SOCKET_EVENTS.CONNECT_ERROR, (error: unknown) => {
      logger.error('Socket connection error', { error }, 'RealSocketService');
      this.connectionReady = false;
    });

    this.socket.on(SOCKET_EVENTS.DISCONNECT, (reason: string) => {
      logger.warn('Socket disconnected', { reason }, 'RealSocketService');
      this.connectionReady = false;
    });

    // Use native socket.io events for reconnection monitoring
    // These are not in SOCKET_EVENTS but are standard socket.io events
    this.socket.on('disconnect', (reason: string) => {
      logger.info('Socket disconnected, will retry', { reason }, 'RealSocketService');
    });

    this.socket.on('connect_error', (error: unknown) => {
      logger.warn('Socket reconnection attempt failed', { error }, 'RealSocketService');
    });

    this.socket.io.on('reconnect_failed', () => {
      logger.error('Socket reconnection failed - maximum attempts reached', {}, 'RealSocketService');
    });

    this.socket.on(SOCKET_EVENTS.RECONNECT, () => {
      logger.info('Socket successfully reconnected', {}, 'RealSocketService');
    });
  }

  /**
   * Establishes connection to the socket server
   * Should be called after component mounting
   */
  setupSocketConnection(): void {
    if (!this.socket.connected) {
      logger.debug('Establishing socket connection', {}, 'RealSocketService');
      this.socket.connect();
    }
  }

  /**
   * Emits an event to the socket server
   * @param event - Name of the event to emit
   * @param data - Data payload to send with the event
   */
  emit(event: string, data: unknown): void {
    if (!this.connectionReady) {
      logger.warn('Attempted to emit event while socket not ready', { event }, 'RealSocketService');
      return;
    }
    logger.debug('Emitting socket event', { event }, 'RealSocketService');
    this.socket.emit(event, data);
  }

  /**
   * Registers an event listener for socket events
   * @param event - Name of the event to listen for
   * @param callback - Function to call when the event occurs
   */
  on(event: string, callback: SocketEventHandler): void {
    this.socket.on(event, (data: unknown) => {
      if (!this.connectionReady && event !== SOCKET_EVENTS.CONNECT) {
        this.eventBuffer.push({event, data, callback});
        return;
      }
      callback(data);
    });
  }

  /**
   * Removes an event listener for the specified event
   * @param event - Name of the event to stop listening for
   */
  off(event: string): void {
    this.socket.off(event);
  }

  /**
   * Disconnects from the socket server if connected
   */
  disconnect(): void {
    if (this.socket.connected) {
      logger.debug('Disconnecting socket', {}, 'RealSocketService');
      this.socket.disconnect();
    }
  }

  /**
   * Checks if the socket is currently connected
   * @returns True if connected, false otherwise
   */
  isConnected(): boolean {
    return this.socket.connected;
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
  reconnect(): void {
    this.socket.disconnect().connect();
  }
}

export default new RealSocketService();

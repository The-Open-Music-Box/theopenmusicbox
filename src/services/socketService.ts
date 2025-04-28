import realSocketService from './realSocketService';

/**
 * Interface defining the required methods for socket service implementations.
 * Both mock and real socket services must implement this interface.
 */
interface SocketService {
  setupSocketConnection(): void;
  emit(event: string, data: any): void;
  on(event: string, callback: (data: any) => void): void;
  off(event: string): void;
  disconnect?(): void;
}

/**
 * Socket Service Wrapper
 * This class provides a unified interface for socket communications,
 * automatically selecting between mock and real implementations based on environment configuration.
 * It also adds error handling and logging to all socket operations.
 */
class SocketServiceWrapper implements SocketService {
  private service: SocketService;

  /**
   * Creates a new socket service wrapper instance
   * Uses either mock or real socket service based on the VUE_APP_USE_MOCK environment variable
   */
  constructor() {
    this.service = realSocketService;
  }

  /**
   * Establishes connection to the socket server
   * Wraps the underlying implementation with error handling
   */
  setupSocketConnection(): void {
    try {
      this.service.setupSocketConnection();
    } catch (error) {
      console.error('Error setting up socket connection:', error);
    }
  }

  /**
   * Emits an event to the socket server
   * @param event - Name of the event to emit
   * @param data - Data payload to send with the event
   */
  emit(event: string, data: any): void {
    try {
      this.service.emit(event, data);
    } catch (error) {
      console.error('Error emitting event:', event, error);
    }
  }

  /**
   * Registers an event listener for socket events
   * @param event - Name of the event to listen for
   * @param callback - Function to call when the event occurs
   */
  on(event: string, callback: (data: any) => void): void {
    try {
      this.service.on(event, callback);
    } catch (error) {
      console.error('Error setting up event listener:', event, error);
    }
  }

  /**
   * Removes an event listener for socket events
   * @param event - Name of the event to stop listening for
   */
  off(event: string): void {
    try {
      this.service.off(event);
    } catch (error) {
      console.error('Error removing event listener:', event, error);
    }
  }

  /**
   * Disconnects from the socket server if connected
   */
  disconnect(): void {
    if (this.service.disconnect) {
      this.service.disconnect();
    }
  }
}

export default new SocketServiceWrapper();
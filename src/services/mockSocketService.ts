// src/services/mockSocketService.ts

/**
 * Mock Socket Service
 * Provides a simulated socket.io implementation for development and testing.
 * Mimics real-time communication without requiring a server connection.
 */

class MockSocketService {
    private listeners = new Map<string, Array<(data: any) => void>>();
    private isConnected = false;

    /**
     * Simulates establishing a socket connection
     * After a short delay, sets the connected state and emits the connect event
     */
    setupSocketConnection() {
      setTimeout(() => {
        this.isConnected = true;
        this.emit('connect', {});
        console.log('Mock socket connected');
      }, 500);
    }

    /**
     * Simulates sending an event to the server
     * For specific events, triggers appropriate mock responses after a delay
     * @param event - Name of the event to emit
     * @param data - Data payload to send with the event
     */
    emit(event: string, data: any) {
      if (!this.isConnected && event !== 'connect') {
        console.warn('Socket not connected');
        return;
      }

      console.log(`Mock socket emitting: ${event}`, data);

      setTimeout(() => {
        switch (event) {
          case 'audio_map_update':
            this.handleAudioMapUpdate(data);
            break;
          case 'message':
            this.triggerEvent('response', {
              status: 'success',
              message: `Mock response to: ${data}`,
              timestamp: new Date().toISOString()
            });
            break;
        }
      }, 300);
    }

    /**
     * Registers an event listener for simulated socket events
     * @param event - Name of the event to listen for
     * @param callback - Function to call when the event occurs
     */
    on(event: string, callback: (data: any) => void) {
      if (!this.listeners.has(event)) {
        this.listeners.set(event, []);
      }
      this.listeners.get(event)?.push(callback);
      console.log(`Mock socket listening for: ${event}`);
    }

    /**
     * Triggers a simulated socket event to all registered listeners
     * @param event - Name of the event to trigger
     * @param data - Data payload to pass to event listeners
     * @private
     */
    private triggerEvent(event: string, data: any) {
      const callbacks = this.listeners.get(event) || [];
      callbacks.forEach(callback => callback(data));
    }

    /**
     * Handles audio map update events with appropriate mock responses
     * @param data - Data payload from the event
     * @private
     */
    private handleAudioMapUpdate(data: any) {
      const mockResponse = {
        files: Array.isArray(data) ? data : [data],
        timestamp: new Date().toISOString(),
        status: 'success'
      };

      this.triggerEvent('audio_map_response', mockResponse);
    }
  }

  export default new MockSocketService();
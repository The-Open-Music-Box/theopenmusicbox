// src/services/socketService.ts

import mockSocketService from './mockSocketService';
import realSocketService from './realSocketService';

// Use environment variable or configuration setting
const USE_MOCK = process.env.VUE_APP_USE_MOCK === 'true' || true;

// Add proper type checking for the service
interface SocketService {
  setupSocketConnection(): void;
  emit(event: string, data: any): void;
  on(event: string, callback: (data: any) => void): void;
  disconnect?(): void;
}

class SocketServiceWrapper implements SocketService {
  private service: SocketService;

  constructor() {
    this.service = USE_MOCK ? mockSocketService : realSocketService;
    console.log(`Using ${USE_MOCK ? 'mock' : 'real'} socket service`);
  }

  setupSocketConnection(): void {
    try {
      this.service.setupSocketConnection();
    } catch (error) {
      console.error('Error setting up socket connection:', error);
    }
  }

  emit(event: string, data: any): void {
    try {
      this.service.emit(event, data);
    } catch (error) {
      console.error('Error emitting event:', event, error);
    }
  }

  on(event: string, callback: (data: any) => void): void {
    try {
      this.service.on(event, callback);
    } catch (error) {
      console.error('Error setting up event listener:', event, error);
    }
  }

  disconnect(): void {
    if (this.service.disconnect) {
      this.service.disconnect();
    }
  }
}

export default new SocketServiceWrapper();
// src/services/socketService.ts

import mockSocketService from './mockSocketService';
import realSocketService from './realSocketService';

const USE_MOCK = true;

const socketService = USE_MOCK ? mockSocketService : realSocketService;

// Types pour la documentation et l'autocomplétion
export interface SocketService {
  setupSocketConnection(): void;
  emit(event: string, data: any): void;
  on(event: string, callback: (data: any) => void): void;
}

export default socketService as SocketService;
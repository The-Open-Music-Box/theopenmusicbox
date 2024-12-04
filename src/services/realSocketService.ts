// src/services/socketService.original.ts

import { io, Socket } from 'socket.io-client'

class RealSocketService {
  private socket: Socket

  constructor() {
    this.socket = io('http://localhost:5001', {
      transports: ['websocket'],
      autoConnect: false,
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5
    })

    // Configuration des gestionnaires d'événements de base
    this.setupBaseHandlers()
  }

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

  setupSocketConnection() {
    if (!this.socket.connected) {
      this.socket.connect()
    }
  }

  emit(event: string, data: any) {
    if (!this.socket.connected) {
      console.warn('Attempting to emit while socket is not connected:', event)
      return
    }
    this.socket.emit(event, data)
  }

  on(event: string, callback: (data: any) => void) {
    this.socket.on(event, callback)
  }

  off(event: string) {
    this.socket.off(event)
  }

  disconnect() {
    if (this.socket.connected) {
      this.socket.disconnect()
    }
  }

  // Méthode utilitaire pour vérifier l'état de la connexion
  isConnected(): boolean {
    return this.socket.connected
  }

  // Méthode pour obtenir l'ID du socket
  // Méthode pour obtenir l'ID du socket
getSocketId(): string | null {
    return this.socket.id || null;
}

  // Méthode pour forcer une reconnexion
  reconnect() {
    this.socket.disconnect().connect()
  }
}

export default new RealSocketService()
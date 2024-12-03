import { io, Socket } from 'socket.io-client'

class SocketService {
  private socket: Socket

  constructor() {
    this.socket = io('http://localhost:5001')
  }

  setupSocketConnection() {
    this.socket.on('connect', () => {
      console.log('Connected to server')
    })

    this.socket.on('disconnect', () => {
      console.log('Disconnected from server')
    })
  }

  emit(event: string, data: any) {
    this.socket.emit(event, data)
  }

  on(event: string, callback: (data: any) => void) {
    this.socket.on(event, callback)
  }
}

export default new SocketService()
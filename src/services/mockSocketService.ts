// src/services/mockSocketService.ts

class MockSocketService {
    private listeners = new Map<string, Array<(data: any) => void>>();
    private isConnected = false;
  
    setupSocketConnection() {
      // Simuler le délai de connexion
      setTimeout(() => {
        this.isConnected = true;
        this.emit('connect', {});
        console.log('Mock socket connected');
      }, 500);
    }
  
    emit(event: string, data: any) {
      if (!this.isConnected && event !== 'connect') {
        console.warn('Socket not connected');
        return;
      }
  
      console.log(`Mock socket emitting: ${event}`, data);
  
      // Simuler le traitement et la réponse
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
      }, 300); // Simuler la latence réseau
    }
  
    on(event: string, callback: (data: any) => void) {
      if (!this.listeners.has(event)) {
        this.listeners.set(event, []);
      }
      this.listeners.get(event)?.push(callback);
      console.log(`Mock socket listening for: ${event}`);
    }
  
    private triggerEvent(event: string, data: any) {
      const callbacks = this.listeners.get(event) || [];
      callbacks.forEach(callback => callback(data));
    }
  
    private handleAudioMapUpdate(data: any) {
      // Simuler la réponse du serveur avec la liste mise à jour
      const mockResponse = {
        files: Array.isArray(data) ? data : [data],
        timestamp: new Date().toISOString(),
        status: 'success'
      };
  
      this.triggerEvent('audio_map_response', mockResponse);
    }
  }
  
  export default new MockSocketService();
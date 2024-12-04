// src/config/index.ts

// Configuration de l'environnement
const config = {
    // API Configuration
    api: {
      baseURL: process.env.VUE_APP_API_URL || 'http://localhost:5001',
      timeout: 30000,
      withCredentials: false
    },
    
    // Socket Configuration
    socket: {
      url: process.env.VUE_APP_SOCKET_URL || 'http://localhost:5001',
      options: {
        transports: ['websocket'],
        autoConnect: false,
        reconnection: true
      }
    },
    
    // Feature Flags
    features: {
      useMockServices: process.env.VUE_APP_USE_MOCK === 'true' || false,
      enableAudioPlayer: true,
      enableFileUpload: true
    },
    
    // Upload Configuration
    upload: {
      maxFileSize: 100 * 1024 * 1024, // 100MB
      allowedTypes: ['audio/mpeg', 'audio/wav', 'audio/ogg'],
      endpoint: '/api/upload'
    },
    
    // Audio Player Configuration
    audio: {
      baseUrl: process.env.VUE_APP_AUDIO_URL || 'http://localhost:5001/audio',
      defaultVolume: 1.0,
      bufferLength: 3
    }
  }
  
  export default config;
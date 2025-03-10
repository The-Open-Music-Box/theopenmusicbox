// src/services/mockData.ts
import { AudioFile, FileStatus, FILE_STATUS, PlayList } from '../components/files/types'

  
  interface Stats {
    battery: number;
    songCount: number;
    freeSpace: number;
  }
  interface ComponentHealth {
    status: string
    timestamp: number
  }
  
  interface SystemHealth {
    components: {
      [key: string]: ComponentHealth
    }
    status: string
    timestamp: number
  }
  
  // Données mockées
  const mockPlaylists: PlayList[] = [
    {
      id: 1,
      name: 'Summer Playlist',
      files: [
        {
          id: 1,
          name: "Summer Vibes.mp3",
          status: FILE_STATUS.ASSOCIATED,
          duration: 180,
          createdAt: "2024-01-15",
          playlistId: 1
        },
        {
          id: 2,
          name: "Guitar Solo.mp3",
          status: FILE_STATUS.IN_PROGRESS,
          duration: 240,
          createdAt: "2024-01-16",
          playlistId: 1
        }
      ]
    },
    {
      id: 2,
      name: 'Classical Music',
      files: [
        {
          id: 3,
          name: "Piano Concert.mp3",
          status: FILE_STATUS.ARCHIVED,
          duration: 360,
          createdAt: "2024-01-17",
          playlistId: 2
        }
      ]
    }
  ]
  
  
  const mockStats: Stats = {
    battery: 71,
    songCount: 12,
    freeSpace: 24
  };
  
  // Service de mock

  class MockDataService {
    private simulateDelay(min = 200, max = 800): Promise<void> {
      const delay = Math.random() * (max - min) + min;
      return new Promise(resolve => setTimeout(resolve, delay));
    }
  
    async getPlaylists(): Promise<PlayList[]> {
      await this.simulateDelay();
      return [...mockPlaylists];
    }
  

  
    async uploadFile(file: File, playlistId = 1): Promise<AudioFile> {
      await this.simulateDelay(1000, 2000);
      
      // Créer le nouveau fichier audio
      const newFile: AudioFile = {
        id: Math.max(...mockPlaylists.flatMap(p => p.files).map(f => f.id)) + 1,
        name: file.name,
        status: FILE_STATUS.IN_PROGRESS,
        duration: Math.floor(Math.random() * 300) + 60,
        createdAt: new Date().toISOString().split('T')[0],
        playlistId
      };
  
      // Trouver la playlist et ajouter le fichier
      const playlist = mockPlaylists.find(p => p.id === playlistId);
      if (playlist) {
        playlist.files.push(newFile);
      } else {
        throw new Error('Playlist not found');
      }
  
      return newFile;
    }
  
    async deleteFile(id: number): Promise<void> {
      await this.simulateDelay();
      for (const playlist of mockPlaylists) {
        const index = playlist.files.findIndex(file => file.id === id);
        if (index !== -1) {
          playlist.files.splice(index, 1);
          return;
        }
      }
      throw new Error('File not found');
    }

    async getStats(): Promise<{
      battery: number;
      songCount: number;
      freeSpace: number;
    }> {
      await this.simulateDelay();
      return {
        battery: 71,
        songCount: mockPlaylists.reduce((count, playlist) => count + playlist.files.length, 0),
        freeSpace: 24
      };
    }
    async checkHealth() {
      await this.simulateDelay();
    const currentTimestamp = Math.floor(Date.now() / 1000);
    
    return {
      components: {
        audio: {
          status: "ready",
          timestamp: currentTimestamp
        },
        config: {
          status: "ready",
          timestamp: currentTimestamp
        },
        gpio: {
          status: "ready",
          timestamp: currentTimestamp
        },
        ir_detector: {
          status: "disabled",
          timestamp: currentTimestamp
        },
        led: {
          status: "disabled",
          timestamp: currentTimestamp
        },
        light_sensor: {
          status: "disabled",
          timestamp: currentTimestamp
        },
        motor: {
          status: "disabled",
          timestamp: currentTimestamp
        },
        nfc: {
          status: "disabled",
          timestamp: currentTimestamp
        }
      },
      status: "healthy",
      timestamp: currentTimestamp
    };
  }

  }
  
  export default new MockDataService();
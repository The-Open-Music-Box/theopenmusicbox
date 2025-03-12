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
  

  
    async uploadFile(file: File | FormData, options?: { 
      headers?: Record<string, string>; 
      onUploadProgress?: (progress: any) => void;
    }, playlistId = 1): Promise<AudioFile> {
      await this.simulateDelay(1000, 2000);
      
      // Handle progress simulation
      if (options?.onUploadProgress) {
        for (let i = 0; i <= 100; i += 20) {
          await this.simulateDelay(100, 200);
          options.onUploadProgress({ progress: i });
        }
      }
    
      const actualFile = file instanceof File ? file : (file.get('file') as File);
      
      // Create new audio file
      const newFile: AudioFile = {
        id: Math.max(...mockPlaylists.flatMap(p => p.files).map(f => f.id)) + 1,
        name: actualFile.name,
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

    async downloadFile(fileId: number, onProgress?: (progress: number) => void) {
      await this.simulateDelay();
      // Simulate download progress
      if (onProgress) {
        for (let i = 0; i <= 100; i += 20) {
          await this.simulateDelay(100, 200);
          onProgress(i);
        }
      }
      return new Blob(['mock file content'], { type: 'audio/mpeg' });
    }

    downloadFileUrl(fileId: number): string {
      return `mock://download/${fileId}`;
    }

    async getUploadSessionId(): Promise<string> {
      await this.simulateDelay();
      const buffer = new Uint16Array(8);
      crypto.getRandomValues(buffer);
      
      return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c, i) {
        const r = (buffer[i % 8] & 0x0F) + 0x01;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
      });
    }
  }
  
  export default new MockDataService();
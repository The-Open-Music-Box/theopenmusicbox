// src/services/mockData.ts
import { AudioFile, FileStatus, FILE_STATUS } from '../components/files/types'

  
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
  const mockAudioFiles: AudioFile[] = [
    {
      id: 1,
      name: "Summer Vibes.mp3",
      status: FILE_STATUS.ASSOCIATED,  // Au lieu de "associer"
      duration: 180,
      createdAt: "2024-01-15"
    },
    {
      id: 2,
      name: "Guitar Solo.mp3",
      status: FILE_STATUS.IN_PROGRESS,  // Au lieu de "In progress"
      duration: 240,
      createdAt: "2024-01-16"
    },
    {
      id: 3,
      name: "Piano Concert.mp3",
      status: FILE_STATUS.ARCHIVED,  // Au lieu de "Archived"
      duration: 360,
      createdAt: "2024-01-17"
    }
  ];
  
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
  
    async getAudioFiles(): Promise<AudioFile[]> {
      await this.simulateDelay();
      return [...mockAudioFiles];
    }
  
    async getStats(): Promise<Stats> {
      await this.simulateDelay();
      return { ...mockStats };
    }
  
    async uploadFile(file: File): Promise<AudioFile> {
      await this.simulateDelay(1000, 2000); // Simulation plus longue pour l'upload
      const newFile: AudioFile = {
        id: mockAudioFiles.length + 1,
        name: file.name,
        status: FILE_STATUS.IN_PROGRESS,
        duration: Math.floor(Math.random() * 300) + 60,
        createdAt: new Date().toISOString().split('T')[0]
      };
      mockAudioFiles.push(newFile);
      return newFile;
    }
  
    async deleteFile(id: number): Promise<void> {
      await this.simulateDelay();
      const index = mockAudioFiles.findIndex(file => file.id === id);
      if (index !== -1) {
        mockAudioFiles.splice(index, 1);
      }
    }
    async checkHealth(): Promise<SystemHealth> {
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
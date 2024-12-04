// src/services/mockData.ts

// Types pour notre application
interface AudioFile {
    id: number;
    name: string;
    status: string;
    duration: number;
    createdAt: string;
  }
  
  interface Stats {
    battery: number;
    songCount: number;
    freeSpace: number;
  }
  
  // Données mockées
  const mockAudioFiles: AudioFile[] = [
    {
      id: 1,
      name: "Summer Vibes.mp3",
      status: "associer",
      duration: 180,
      createdAt: "2024-01-15"
    },
    {
      id: 2,
      name: "Guitar Solo.mp3",
      status: "In progress",
      duration: 240,
      createdAt: "2024-01-16"
    },
    {
      id: 3,
      name: "Piano Concert.mp3",
      status: "Archived",
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
        status: "In progress",
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
    async checkHealth() {
      await this.simulateDelay()
      return { status: 'ok', message: 'Mock server is healthy' }
    }
  }
  
  export default new MockDataService();
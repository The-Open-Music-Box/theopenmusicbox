// src/services/mockData.ts
import {
  PlayList,
  Track,
  Hook,
  LegacyAudioFile,
  FILE_STATUS,
  LegacyPlayList,
  playlistToLegacy
} from '../components/files/types'

interface Stats {
  battery: number;
  track_count: number;
  free_space_percent: number;
}

interface ComponentHealth {
  status: string
  timestamp: number
}

// Interface used in the health check function
interface SystemHealthResponse {
  components: {
    [key: string]: ComponentHealth
  }
  status: string
  timestamp: number
}

// Progress interface for upload tracking
interface UploadProgress {
  progress: number;
}

// Backend-style mock data
const mockBackendData: (PlayList | Hook)[] = [
  {
    id: "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
    type: "playlist",
    title: "Zelda & Sleep",
    description: "Zelda theme sleep music",
    tracks: [
      {
        number: 1,
        title: "Ocarina of Time",
        filename: "Zelda & Sleep - 001 Ocarina of Time [MTrZXHaXPrU].mp3",
        duration: "180",
        play_counter: 0
      },
      {
        number: 2,
        title: "Zelda's Lullaby",
        filename: "Zelda & Sleep - 002 Zelda's Lullaby [MTrZXHaXPrU].mp3",
        duration: "240",
        play_counter: 0
      }
    ],
    created_at: "2024-02-12T14:30:00Z",
    last_played: Date.parse("2024-02-12T15:00:00Z") / 1000 // Convert to timestamp
  },
  {
    id: "7ba7b810-9dad-11d1-80b4-00c04fd430c8",
    type: "hook",
    idtagnfc: "04912ba5df6180",
    path: "http://homeassistant.local:8123/api/webhook/--un1U88dYVP9nhgvcGt2J1nD",
    created_at: "2024-02-12T14:30:00Z"
  }
];

// Export stats for use by other services
export const mockSystemStats: Stats = {
  battery: 71,
  track_count: mockBackendData.reduce((count, item) =>
    item.type === 'playlist' ? count + (item as PlayList).tracks.length : count, 0),
  free_space_percent: 24
};

export const mockSystemHealth: SystemHealthResponse = {
  components: {
    audio: {
      status: "ready",
      timestamp: Math.floor(Date.now() / 1000)
    },
    config: {
      status: "ready",
      timestamp: Math.floor(Date.now() / 1000)
    },
    gpio: {
      status: "ready",
      timestamp: Math.floor(Date.now() / 1000)
    },
    ir_detector: {
      status: "disabled",
      timestamp: Math.floor(Date.now() / 1000)
    },
    led: {
      status: "disabled",
      timestamp: Math.floor(Date.now() / 1000)
    },
    light_sensor: {
      status: "disabled",
      timestamp: Math.floor(Date.now() / 1000)
    },
    motor: {
      status: "disabled",
      timestamp: Math.floor(Date.now() / 1000)
    },
    nfc: {
      status: "disabled",
      timestamp: Math.floor(Date.now() / 1000)
    }
  },
  status: "healthy",
  timestamp: Math.floor(Date.now() / 1000)
};

// Mock data service
class MockDataService {
  private simulateDelay(min = 200, max = 800): Promise<void> {
    const delay = Math.random() * (max - min) + min;
    return new Promise(resolve => setTimeout(resolve, delay));
  }

  async getPlaylists(): Promise<LegacyPlayList[]> {
    await this.simulateDelay();
    return mockBackendData
      .filter((item): item is PlayList => item.type === 'playlist')
      .map(playlist => playlistToLegacy(playlist));
  }

  async getAudioFiles() {
    await this.simulateDelay();
    const allTracks = mockBackendData
      .filter((item): item is PlayList => item.type === 'playlist')
      .flatMap(playlist => playlist.tracks.map(track => ({
        id: track.number,
        name: track.filename,
        status: FILE_STATUS.ASSOCIATED,
        duration: parseInt(track.duration),
        createdAt: new Date().toISOString(),
        playlistId: parseInt(playlist.id),
        isAlbum: false
      })));
    return allTracks;
  }

  async uploadFile(file: File | FormData, options?: {
    headers?: Record<string, string>;
    onUploadProgress?: (progress: UploadProgress) => void;
  }, playlistId = "1"): Promise<LegacyAudioFile> {
    await this.simulateDelay(1000, 2000);

    if (options?.onUploadProgress) {
      for (let i = 0; i <= 100; i += 20) {
        await this.simulateDelay(100, 200);
        options.onUploadProgress({ progress: i });
      }
    }

    const actualFile = file instanceof File ? file : (file.get('file') as File);

    const playlist = mockBackendData.find(item =>
      item.type === 'playlist' && item.id === playlistId) as PlayList | undefined;

    if (!playlist) {
      throw new Error('Playlist not found');
    }

    const newTrack: Track = {
      number: playlist.tracks.length + 1,
      title: actualFile.name.split('.')[0],
      filename: actualFile.name,
      duration: Math.floor(Math.random() * 300 + 60).toString(),
      play_counter: 0
    };

    playlist.tracks.push(newTrack);

    return {
      id: String(newTrack.number), // Convert number to string explicitly
      name: newTrack.filename,
      status: FILE_STATUS.IN_PROGRESS,
      size: 1024 * 1024, // Add missing property
      type: "audio/mpeg", // Add missing property
      path: `/uploads/${newTrack.filename}`,
      uploaded: new Date().toISOString(),
      metadata: {
        duration: parseInt(newTrack.duration),
        createdAt: new Date().toISOString(),
        playlistId: parseInt(playlistId),
        isAlbum: false
      }
    };
  }

  async deleteFile(id: number): Promise<void> {
    await this.simulateDelay();
    for (const item of mockBackendData) {
      if (item.type === 'playlist') {
        const playlist = item as PlayList;
        const index = playlist.tracks.findIndex(track => track.number === id);
        if (index !== -1) {
          playlist.tracks.splice(index, 1);
          return;
        }
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
      songCount: mockBackendData.reduce((count, item) =>
        item.type === 'playlist' ? count + (item as PlayList).tracks.length : count, 0),
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
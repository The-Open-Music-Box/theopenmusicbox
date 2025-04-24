/**
 * Mock Data Service
 * Provides simulated API responses for development and testing.
 * Contains mock data structures and methods that mimic API behavior without requiring a backend.
 */

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

interface SystemHealthResponse {
  components: {
    [key: string]: ComponentHealth
  }
  status: string
  timestamp: number
}

interface UploadProgress {
  progress: number;
}

/**
 * Mock backend data representing playlists and hooks
 */
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
    last_played: Date.parse("2024-02-12T15:00:00Z") / 1000
  },
  {
    id: "7ba7b810-9dad-11d1-80b4-00c04fd430c8",
    type: "hook",
    idtagnfc: "04912ba5df6180",
    path: "http://homeassistant.local:8123/api/webhook/--un1U88dYVP9nhgvcGt2J1nD",
    created_at: "2024-02-12T14:30:00Z"
  }
];

/**
 * Mock system statistics
 */
export const mockSystemStats: Stats = {
  battery: 71,
  track_count: mockBackendData.reduce((count, item) =>
    item.type === 'playlist' ? count + (item as PlayList).tracks.length : count, 0),
  free_space_percent: 24
};

/**
 * Mock system health status
 */
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

/**
 * Service for providing mock data responses
 * Simulates backend API behavior for development and testing
 */
class MockDataService {
  /**
   * Simulates network delay with random duration
   * @param min - Minimum delay in milliseconds (default: 200)
   * @param max - Maximum delay in milliseconds (default: 800)
   * @returns Promise that resolves after the delay period
   * @private
   */
  private simulateDelay(min = 200, max = 800): Promise<void> {
    const delay = Math.random() * (max - min) + min;
    return new Promise(resolve => setTimeout(resolve, delay));
  }

  /**
   * Fetches mock playlist data
   * @returns Promise resolving to array of playlists in legacy format
   */
  async getPlaylists(): Promise<LegacyPlayList[]> {
    await this.simulateDelay();
    return mockBackendData
      .filter((item): item is PlayList => item.type === 'playlist')
      .map(playlist => playlistToLegacy(playlist));
  }

  /**
   * Fetches mock audio files data
   * @returns Promise resolving to array of audio files
   */
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

  /**
   * Simulates file upload process with progress updates
   * @param file - File or FormData object to upload
   * @param options - Optional configuration including progress callback
   * @param playlistId - Target playlist ID for the upload
   * @returns Promise resolving to the uploaded file data
   */
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
      id: String(newTrack.number),
      name: newTrack.filename,
      status: FILE_STATUS.IN_PROGRESS,
      size: 1024 * 1024,
      type: "audio/mpeg",
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

  /**
   * Simulates deleting a track from a playlist
   * @param playlistId - ID of the playlist
   * @param trackId - ID (or number) of the track to delete
   * @returns Promise that resolves when the delete operation completes
   */
  async deleteTrack(playlistId: string, trackId: string | number): Promise<void> {
    await this.simulateDelay();
    const playlist = mockBackendData.find(
      (item): item is PlayList => item.type === 'playlist' && item.id === playlistId
    );
    if (!playlist) throw new Error('Playlist not found');
    const index = playlist.tracks.findIndex(track => String(track.number) === String(trackId));
    if (index !== -1) {
      playlist.tracks.splice(index, 1);
      return;
    }
    throw new Error('Track not found');
  }

  /**
   * Fetches mock system statistics
   * @returns Promise resolving to system statistics
   */
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

  /**
   * Checks mock system health status
   * @returns Promise resolving to system health data
   */
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

  /**
   * Simulates downloading a file with progress updates
   * @param fileId - ID of the file to download
   * @param onProgress - Optional callback for tracking download progress
   * @returns Promise resolving to a mock file blob
   */
  async downloadFile(fileId: number, onProgress?: (progress: number) => void) {
    await this.simulateDelay();
    if (onProgress) {
      for (let i = 0; i <= 100; i += 20) {
        await this.simulateDelay(100, 200);
        onProgress(i);
      }
    }
    return new Blob(['mock file content'], { type: 'audio/mpeg' });
  }

  /**
   * Generates a mock download URL for a file
   * @param fileId - ID of the file
   * @returns Mock URL string for downloading the file
   */
  downloadFileUrl(fileId: number): string {
    return `mock://download/${fileId}`;
  }

  /**
   * Generates a mock upload session ID
   * Creates a UUID v4 style identifier for tracking uploads
   * @returns Promise resolving to session ID string
   */
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
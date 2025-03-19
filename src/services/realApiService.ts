// src/services/realApiService.ts

import axios, { AxiosError, InternalAxiosRequestConfig, AxiosResponse, AxiosProgressEvent } from 'axios'

// Configuration de base d'axios pour notre API
const apiClient = axios.create({
  baseURL: process.env.VUE_APP_API_URL,
  timeout: 60000,
  headers: {
    Accept: 'application/json',
    'Content-Type': 'application/json'
  }
})

// Implémenter un système de cache pour les données fréquemment accédées
const cache = new Map()

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

// Ajouter des métriques de performance
const metrics = {
  requestCount: 0,
  errorCount: 0,
  averageResponseTime: 0
}

// Étendre le type de configuration Axios pour inclure nos métadonnées
declare module 'axios' {
  export interface InternalAxiosRequestConfig {
    metadata?: {
      start: number
    }
  }
}

// Implémenter la logique de retry manuellement
const retryRequest = async (error: AxiosError, retries = 3, delay = 1000): Promise<AxiosResponse> => {
  const config = error.config
  if (!config || !retries) {
    return Promise.reject(error)
  }

  await new Promise(resolve => setTimeout(resolve, delay))
  return apiClient(config)
}

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  config.metadata = { start: Date.now() }
  return config
})

apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    const duration = Date.now() - (response.config.metadata?.start || 0)
    metrics.requestCount++
    metrics.averageResponseTime = (metrics.averageResponseTime * (metrics.requestCount - 1) + duration) / metrics.requestCount
    return response
  },
  async (error: AxiosError) => {
    metrics.errorCount++

    // Tenter le retry si c'est une erreur réseau ou 5xx
    if (error.response?.status && error.response.status >= 500) {
      try {
        return await retryRequest(error)
      } catch (retryError) {
        return Promise.reject(retryError)
      }
    }

    return Promise.reject(error)
  }
)

class RealApiService {
  async getAudioFiles() {
    const cacheKey = 'audio_files'
    if (cache.has(cacheKey)) {
      return cache.get(cacheKey)
    }
    try {
      console.log('Fetching audio files from API...')
      const response = await apiClient.get('/api/nfc_mapping')
      console.log('Audio files response:', response.data)

      // Les données sont déjà au bon format, pas besoin de transformation
      const playlists = response.data
      console.log('Playlists transformées:', playlists)

      cache.set(cacheKey, playlists)
      return playlists
    } catch (err) {
      const error = err as AxiosError
      console.error('Error fetching audio files:', {
        response: error.response?.data,
        status: error.response?.status,
        headers: error.response?.headers
      })
      if (error.response?.status === 401) {
        // Gérer l'authentification
      } else if (error.response?.status === 503) {
        // Gérer la maintenance
      }
      throw error
    }
  }

  async uploadFile(file: File | FormData, options?: {
    headers?: Record<string, string>;
    onUploadProgress?: (progress: AxiosProgressEvent) => void;
  }) {
    const formData = file instanceof File ? (() => {
      const fd = new FormData();
      fd.append('file', file);
      return fd;
    })() : file;

    try {
      const response = await apiClient.post('api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          ...options?.headers
        },
        onUploadProgress: options?.onUploadProgress
      });
      return response.data;
    } catch (error) {
      console.error('Error uploading file:', error);
      throw error;
    }
  }

  async deleteFile(id: number) {
    try {
      const response = await apiClient.post('/api/remove_file', { id })
      return response.data
    } catch (error) {
      console.error('Error deleting file:', error)
      throw error
    }
  }

  async getStats() {
    try {
      const response = await apiClient.get('api/stats')
      return response.data
    } catch (error) {
      console.error('Error fetching stats:', error)
      throw error
    }
  }

  async checkHealth(): Promise<SystemHealth> {
    try {
      console.log('Fetching health status...')
      const response = await apiClient.get('health')
      console.log('Health response:', response)
      return response.data
    } catch (err) {
      const error = err as AxiosError
      console.error('Error fetching health status:', {
        response: error.response?.data,
        status: error.response?.status,
        headers: error.response?.headers
      })
      throw error
    }
  }

  async downloadFile(fileId: number, onProgress?: (progress: number) => void) {
    try {
      const response = await apiClient.get(`/api/audio/download/${fileId}`, {
        responseType: 'blob',
        onDownloadProgress: (progressEvent) => {
          if (onProgress && progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            onProgress(progress)
          }
        }
      })
      return response.data
    } catch (error) {
      console.error('Error downloading file:', error)
      throw error
    }
  }

  downloadFileUrl(fileId: number): string {
    return `${apiClient.defaults.baseURL}/api/audio/download/${fileId}`
  }

  async getUploadSessionId(): Promise<string> {
    try {
      const response = await apiClient.post('/api/upload/session')
      return response.data.sessionId
    } catch (error) {
      console.error('Error getting upload session:', error)
      throw error
    }
  }
}

export default new RealApiService()
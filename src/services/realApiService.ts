// src/services/realApiService.ts

import axios, { AxiosError } from 'axios'

// Configuration de base d'axios pour notre API
const apiClient = axios.create({
  baseURL: process.env.VUE_APP_API_URL,
  headers: {
    Accept: 'application/json',
    'Content-Type': 'application/json'
  },
  timeout: 5000 // 5 seconds timeout for health check
})

// interface HealthCheckResponse {
//   status: 'ok' | 'error'
//   message: string
//   timestamp?: string
//   version?: string
// }
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


class RealApiService {
  async getAudioFiles() {
    try {
      console.log('Fetching audio files from API...')
      const response = await apiClient.get('/api/audio/files')
      console.log('Audio files response:', response)
      return response.data.files || []
    } catch (err) {
      const error = err as AxiosError
      console.error('Error fetching audio files:', {
        response: error.response?.data,
        status: error.response?.status,
        headers: error.response?.headers
      })
      throw error
    }
  }

  async uploadFile(file: File | FormData, options?: { 
    headers?: Record<string, string>; 
    onUploadProgress?: (progress: any) => void;
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

  // async checkHealth(): Promise<HealthCheckResponse> {
  //   try {
  //     const response = await apiClient.get('api/health')
  //     return {
  //       status: response.data.status || 'ok',
  //       message: response.data.message || 'Service is healthy',
  //       timestamp: new Date().toISOString(),
  //       version: response.data.version
  //     }
  //   } catch (error) {
  //     console.error('Health check error:', error)
  //     const errorResponse: HealthCheckResponse = {
  //       status: 'error',
  //       message: 'Service is unavailable',
  //       timestamp: new Date().toISOString()
  //     }
  //     throw errorResponse
  //   }
  // }
  async checkHealth(): Promise<SystemHealth> {
    try {
      const response = await apiClient.get('/api/system/health')
      console.log('Health check response:', response)
      return {
        components: response.data.components,
        status: response.data.status,
        timestamp: response.data.timestamp
      }
    } catch (err) {
      // Type l'erreur comme AxiosError
      const error = err as AxiosError
      console.log('Full error details:', {
        response: error.response?.data,
        status: error.response?.status,
        headers: error.response?.headers
      })
  
      throw {
        components: {},
        status: 'error',
        timestamp: Date.now() / 1000
      }
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
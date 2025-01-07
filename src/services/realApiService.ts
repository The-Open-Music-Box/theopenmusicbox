// src/services/realApiService.ts

import axios from 'axios'

// Configuration de base d'axios pour notre API
const apiClient = axios.create({
  baseURL: 'http://localhost:5001/',
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
      const response = await apiClient.get('api/get_audio_files')
      return response.data.audio_files
    } catch (error) {
      console.error('Error fetching audio files:', error)
      throw error
    }
  }

  async uploadFile(file: File) {
    const formData = new FormData()
    formData.append('file', file)
    
    try {
      const response = await apiClient.post('api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      return response.data
    } catch (error) {
      console.error('Error uploading file:', error)
      throw error
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
      const response = await apiClient.get('system/health')
      return response.data
    } catch (error) {
      console.error('Health check error:', error)
      throw {
        components: {},
        status: 'error',
        timestamp: Date.now() / 1000
      }
    }

}
}

export default new RealApiService()
// src/services/realApiService.ts

import axios from 'axios'

// Configuration de base d'axios pour notre API
const apiClient = axios.create({
  baseURL: 'http://localhost:5001/',
  headers: {
    Accept: 'application/json',
    'Content-Type': 'application/json'
  }
})

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
}

export default new RealApiService()
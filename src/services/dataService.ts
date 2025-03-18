// src/services/dataService.ts

import mockDataService from './mockData'
import realApiService from './realApiService'
interface UploadOptions {
  headers?: Record<string, string>;
  onUploadProgress?: (progress: any) => void;
}
const USE_MOCK = process.env.VUE_APP_USE_MOCK === 'true' // Variable pour basculer entre mock et réel

// Service qui fait le pont entre les composants et la source de données
const dataService = {
  async checkHealth() {
    return USE_MOCK 
      ? mockDataService.checkHealth()
      : realApiService.checkHealth()
  },

  getPlaylists() {
    return USE_MOCK 
      ? mockDataService.getAudioFiles()
      : realApiService.getAudioFiles()
  },

  uploadFile(file: File | FormData, options?: UploadOptions) {
    return USE_MOCK 
      ? mockDataService.uploadFile(file, options)
      : realApiService.uploadFile(file, options)
  },

  deleteFile(id: number) {
    return USE_MOCK 
      ? mockDataService.deleteFile(id)
      : realApiService.deleteFile(id)
  },

  getStats() {
    return USE_MOCK 
      ? mockDataService.getStats()
      : realApiService.getStats()
  },

  downloadFile(fileId: number, onProgress?: (progress: number) => void) {
    return USE_MOCK
      ? mockDataService.downloadFile(fileId, onProgress)
      : realApiService.downloadFile(fileId, onProgress)
  },

  downloadFileUrl(fileId: number) {
    return USE_MOCK
      ? mockDataService.downloadFileUrl(fileId)
      : realApiService.downloadFileUrl(fileId)
  },

  getUploadSessionId() {
    return USE_MOCK
      ? mockDataService.getUploadSessionId()
      : realApiService.getUploadSessionId()
  }
}

export default dataService
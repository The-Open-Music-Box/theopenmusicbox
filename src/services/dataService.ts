// src/services/dataService.ts

import mockDataService from './mockData'
import realApiService from './realApiService'

const USE_MOCK = process.env.VUE_APP_USE_MOCK === 'true' // Variable pour basculer entre mock et réel

// Service qui fait le pont entre les composants et la source de données
const dataService = {
  async checkHealth() {
    return USE_MOCK 
      ? mockDataService.checkHealth()
      : realApiService.checkHealth()
  },

  getAudioFiles() {
    return USE_MOCK 
      ? mockDataService.getAudioFiles()
      : realApiService.getAudioFiles()
  },

  uploadFile(file: File) {
    return USE_MOCK 
      ? mockDataService.uploadFile(file)
      : realApiService.uploadFile(file)
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

}

export default dataService
// src/services/api.ts
import axios, { AxiosProgressEvent, AxiosRequestConfig } from 'axios'
import config from '../config'

// Création du client axios avec la configuration de base
const apiClient = axios.create({
  baseURL: config.api.baseURL,
  timeout: config.api.timeout,
  withCredentials: config.api.withCredentials,
  headers: {
    Accept: 'application/json',
    'Content-Type': 'multipart/form-data',
  },
})

// Configuration de l'intercepteur pour la gestion globale des erreurs
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Gestion détaillée des erreurs selon leur type
    if (error.response) {
      console.error('Server Error:', {
        status: error.response.status,
        data: error.response.data,
        endpoint: error.config.url,
        method: error.config.method
      })
    } else if (error.request) {
      console.error('Network Error:', {
        endpoint: error.config.url,
        error: error.message
      })
    } else {
      console.error('Configuration Error:', error.message)
    }
    
    // Propagation de l'erreur pour la gestion locale
    return Promise.reject(error)
  }
)

// Interface pour définir les types acceptés pour l'upload
interface UploadableFile {
  file: File | Blob;
  filename?: string;
}

// Service API avec les méthodes existantes
export default {
  // Méthode GET générique
  async get(endpoint: string) {
    try {
      const response = await apiClient.get(endpoint)
      return response.data
    } catch (error) {
      // On peut simplifier ce log car l'intercepteur gère déjà le détail
      console.error('GET request error for endpoint:', endpoint)
      throw error
    }
  },

  // Méthode d'upload de fichiers
  async uploadFiles(uploadable: File | Blob) {
    const formData = new FormData()
    
    // Si c'est un File, on peut accéder au nom
    const filename = uploadable instanceof File ? uploadable.name : 'unnamed-file'
    formData.append('file', uploadable, filename)

    try {
      const response = await apiClient.post('api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        // Ajout optionnel du suivi de progression
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            console.log(`Upload progress: ${progress}%`)
          }
        }
      })
      return response.data
    }  catch (error) {
      console.error('File upload error for file:', filename)
      throw error
    }
  },

  // Vous pouvez ajouter d'autres méthodes selon vos besoins
  async post(endpoint: string, data: any, config?: AxiosRequestConfig) {
    try {
      const response = await apiClient.post(endpoint, data, config)
      return response.data
    } catch (error) {
      console.error('POST request error for endpoint:', endpoint)
      throw error
    }
  }
}
/**
 * API Service
 * Provides methods to interact with the backend API
 * Handles HTTP requests, error handling, and file uploads
 */
import axios, { AxiosProgressEvent, AxiosRequestConfig } from 'axios'
import config from '../config'

const apiUrl = process.env.VUE_APP_API_URL;
const apiPort = process.env.VUE_APP_SRVE_PORT;

/**
 * Axios instance configured with base URL, timeout and credentials settings
 */
const apiClient = axios.create({
  baseURL: `${apiUrl}:${apiPort}`,
  timeout: config.api.timeout,
  withCredentials: config.api.withCredentials,
  headers: {
    Accept: 'application/json',
    'Content-Type': 'multipart/form-data',
  },
})

/**
 * Response interceptor to handle and log API errors
 */
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
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
    return Promise.reject(error)
  }
)

/**
 * Interface for files that can be uploaded to the API
 */
interface UploadableFile {
  file: File | Blob;
  filename?: string;
}

export default {
  /**
   * Performs a GET request to the specified API endpoint
   *
   * @param endpoint - The API endpoint to request
   * @returns The response data from the API
   * @throws Error if the request fails
   */
  async get(endpoint: string) {
    try {
      const response = await apiClient.get(endpoint)
      return response.data
    } catch (error) {
      console.error('GET request error for endpoint:', endpoint)
      throw error
    }
  },

  /**
   * Uploads a file to the server
   *
   * @param uploadable - The file to upload (File or Blob)
   * @returns The response data from the API
   * @throws Error if the upload fails
   */
  async uploadFiles(uploadable: File | Blob) {
    const formData = new FormData()

    const filename = uploadable instanceof File ? uploadable.name : 'unnamed-file'
    formData.append('file', uploadable, filename)

    try {
      const response = await apiClient.post('api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
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

  /**
   * Performs a POST request to the specified API endpoint
   *
   * @param endpoint - The API endpoint to send data to
   * @param data - The data to send in the request body
   * @param config - Optional Axios request configuration
   * @returns The response data from the API
   * @throws Error if the request fails
   */
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
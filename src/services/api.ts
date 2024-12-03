import axios from 'axios'

const apiClient = axios.create({
  baseURL: 'http://localhost:5001/',
  withCredentials: false,
  headers: {
    Accept: 'application/json',
    'Content-Type': 'multipart/form-data',
  },
})

export default {
  async get(endpoint: string) {
    try {
      const response = await apiClient.get(endpoint)
      return response.data
    } catch (error) {
      console.error('GET request error:', error)
      throw error
    }
  },

  async uploadFiles(file: Blob) {
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await apiClient.post('api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      return response.data
    } catch (error) {
      console.error('File upload error:', error)
      throw error
    }
  },
}

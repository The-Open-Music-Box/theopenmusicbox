/**
 * Mock API Client
 * This module provides a simple mock implementation of API endpoints for development purposes.
 * It simulates network delays and API responses without requiring a real backend.
 */

export const apiClient = {
  /**
   * Simulates a GET request to an API endpoint
   * @param endpoint - The API endpoint path to request
   * @returns Promise resolving to the mock response data
   * @example
   * apiClient.get('/data')
   *   .then(response => console.log(response.data))
   *   .catch(error => console.error(error))
   */
  get(endpoint: string) {
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        if (endpoint === '/data') {
          resolve({
            data: { message: 'Data fetched successfully' },
          })
        } else {
          reject(new Error('Endpoint not found'))
        }
      }, 500)
    })
  },

  /**
   * Simulates file upload functionality
   * @param formData - FormData object containing files to be uploaded
   * @returns Promise resolving to the mock response data
   * @example
   * const formData = new FormData();
   * formData.append('file', fileObject);
   * apiClient.uploadFiles(formData)
   *   .then(response => console.log(response.data))
   *   .catch(error => console.error(error))
   */
  uploadFiles(formData: FormData) {
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        if (formData) {
          resolve({
            data: { message: 'Files uploaded successfully' },
          })
        } else {
          reject(new Error('No files provided'))
        }
      }, 1000)
    })
  },
}

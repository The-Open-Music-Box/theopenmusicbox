// src/services/data.js

export const apiClient = {
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

/**
 * Unit tests for apiClient.ts
 *
 * Tests the base API client and response handlers including:
 * - Axios client configuration and interceptors
 * - Standardized error handling and custom error class
 * - Response data extraction and format handling
 * - Request/response logging and metadata
 * - Performance monitoring and timeout handling
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import axios, { AxiosError, AxiosResponse, InternalAxiosRequestConfig } from 'axios'
import { apiClient, ApiResponseHandler, StandardApiError } from '@/services/api/apiClient'

// Mock axios
vi.mock('axios', () => ({
  default: {
    create: vi.fn(),
    isAxiosError: vi.fn()
  }))

// Mock logger
const mockLogger = {
  debug: vi.fn(),
  info: vi.fn(),
  warn: vi.fn(),
  error: vi.fn()
}

vi.mock('@/utils/logger', () => ({
  logger: mockLogger
}))

// Mock config
vi.mock('@/config/environment', () => ({
  apiConfig: {
    baseUrl: 'http://localhost:8000/api',
    timeout: 10000,
    withCredentials: true
  })

// Mock types
vi.mock('@/types/contracts', () => ({
  // Contract types are used for typing only
  }
)

describe('StandardApiError', () => {
  it('should create error with all properties', (() => {
    const error = new StandardApiError('Test error message',
      'validation_error',
      400,
      

      { field: 'email', code: 'INVALID_EMAIL' }
      ]

      expect(error.message)
      toBe('Test error message')

      expect(error.errorType)
      toBe('validation_error')
      expect(error.statusCode)
      toBe(400)

      expect(error.details)
      toEqual({ field: 'email', code: 'INVALID_EMAIL' }
      ]

      expect(error.requestId)
      toBe('req-123')

      expect(error.name)
      toBe('StandardApiError')

  it('should check error type correctly', () => {
    const error = new StandardApiError('Test', 'validation_error', 400) 

    expect(error.isType('validation_error')
      toBe(true)
    expect(error.isType('network_error')
      toBe(false)
  }
)
  it('should ident  ify retryable errors', () => {
    const serverError = new StandardApiError('Server error', 'internal_error', 500) 

    const rateLimitError = new StandardApiError('Rate limit', 'rate_limit_exceeded', 429)
      const clientError = new StandardApiError('Bad request', 'validation_error', 400) 

    expect(serverError.isRetryable()
      toBe(true)
    expect(rateLimitError.isRetryable()
      toBe(true)
    expect(clientError.isRetryable()
      toBe(false)
  }
)
  }
)

describe('ApiResponseHandler', () => {
  describe('extractData', () => {
    it('should extract data from successful response', (() => {
      const response =  

        status: 200,
      data: {
  status: 'success'

          data: { id: 1, name: 'Test Item' 
   
} as AxiosResponse

      const result = ApiResponseHandler.extractData(response) 

      expect(result)
      toEqual({ id: 1, name)
    it('should handle 204 No Content responses', () => {
      const response =  

        status: 204

        data: null
   
} as AxiosResponse

      const result = ApiResponseHandler.extractData(response) 

      expect(result)
      toBeUndefined()
  }
)
    it('should handle successful response without data field', () => {
      const response =  

        status: 200,
      data: {
  status: 'success'
} as AxiosResponse

      const result = ApiResponseHandler.extractData(response) 

      expect(result)
      toBeUndefined()
  }
)
    it('should handle direct data responses (legacy support)', () => {
      const directData =  

      { id: 1, title: 'Direct Response' ,
  const response =  

        status: 200

        data: directData
   
} as AxiosResponse

      const result = ApiResponseHandler.extractData(response) 

      expect(result)
      toEqual(directData)
  }
)
    it('should throw StandardApiError  for error responses', () => {
      const response =  

        status: 400,
        data: {
  status: 'error',
          message: 'Validation failed'

  error_type: 'validation_error'

          details: { field: 'email' ,

          request_id: 'req-456'
        
} as AxiosResponse

      expect(() => ApiResponseHandler.extractData(response)
      toThrow(StandardApiError)
      try {
        ApiResponseHandler.extractData(response)
      } catch (error) {
        expect(error)
      toBeInstanceOf(StandardApiError)

      expect((error as StandardApiError)
      message)
      toBe('Validation failed')

      expect((error as StandardApiError)
      errorType)
      toBe('validation_error')

      expect((error as StandardApiError)
      statusCode)
      toBe(400)

      expect((error as StandardApiError)
      details)
      toEqual({ field)

      expect((error as StandardApiError)
      requestId)
      toBe('req-456')
    it('should handle empty response data  for successful status', () => {
      const response =  

        status: 200

        data: null
   
} as AxiosResponse

      const result = ApiResponseHandler.extractData(response) 

      expect(result)
      toBeUndefined()
  }
)
    it('should throw error  for empty response data with error status', () => {
      const response =  

        status: 500,
      data: null
} as AxiosResponse

      expect(() => ApiResponseHandler.extractData(response)
      toThrow(StandardApiError)
      try {
        ApiResponseHandler.extractData(response)
      } catch (error) {
        expect((error as StandardApiError)
      message)
      toBe('Empty response from server')

      expect((error as StandardApiError)
      errorType)
      toBe('internal_error')

      expect((error as StandardApiError)
      statusCode)
      toBe(500)
  }
)
    it('should handle un  expected response format with warning', () => {
      const response =  

        status: 200,
        data: {
  unexpected: 'format'

  without: 'status'
} as AxiosResponse

      const result = ApiResponseHandler.extractData(response) 

      expect(result)
      toEqual({ unexpected: 'format', without)

      expect(mockLogger.warn)
      toHaveBeenCalledWith()
        'Unexpected API response format',
        expect.objectContaining({
          status: 200

          data: { unexpected: 'format', without)),
        'ApiResponseHandler'
  }
)
  }
)

describe('handleError', () => {
    it('should handle server response errors', (() => {
      const axiosError =  

        response: {
  status: 404,
          statusText: 'Not Found',
          data: {
  message: 'Resource not found'

  error_type: 'not_found'

            details: { resource: 'playlist' ,

            request_id: 'req-789'
          
},
        config: {
  method: 'get'

  url: '/api/playlists/123'

          metadata: { start: Date.now() - 100 
   
} as AxiosError

      expect(() => ApiResponseHandler.handleError(axiosError)
      toThrow(StandardApiError)
      try {
        ApiResponseHandler.handleError(axiosError)
      } catch (error) {
        expect(error)
      toBeInstanceOf(StandardApiError)

      expect((error as StandardApiError)
      message)
      toBe('Resource not found')

      expect((error as StandardApiError)
      errorType)
      toBe('not_found')

      expect((error as StandardApiError)
      statusCode)
      toBe(404)

      expect((error as StandardApiError)
      details)
      toEqual({ resource)

      expect((error as StandardApiError)
      requestId)
      toBe('req-789')

      expect(mockLogger.error)
      toHaveBeenCalledWith()
        'API Request failed with server error',
        expect.objectContaining({
          method: 'GET',
          url: '/api/playlists/123',
          status: 404,
          statusText: 'Not Found'

          duration)),
        'ApiClient'
  }
)
    it('should handle network errors (no response)', () => {
      const axiosError =  

      {}
        request: {

        config: {
  method: 'post'

          url: '/api/playlists'

  metadata: { start: Date.now() - 200 
},
        message: 'Network Error'

  as AxiosError

      expect(() => ApiResponseHandler.handleError(axiosError)
      toThrow(StandardApiError)
      try {
        ApiResponseHandler.handleError(axiosError)
      
} catch (error) {
        expect(error)
      toBeInstanceOf(StandardApiError)

      expect((error as StandardApiError)
      message)
      toBe('Network error - unable to reach server')

      expect((error as StandardApiError)
      errorType)
      toBe('network_error')

      expect((error as StandardApiError)
      statusCode)
      toBe(0)

      expect((error as StandardApiError)
      details)
      toEqual({ originalError)

      expect(mockLogger.error)
      toHaveBeenCalledWith()
        'API Request failed - no response received',
        expect.objectContaining({
          method: 'POST',
          url: '/api/playlists',
          error: 'Network Error'

          duration)),
        'ApiClient'
  }
)
    it('should handle request configuration errors', () => {
      const axiosError =  

        config: {
  method: 'put'

  url: '/api/playlists/123'
},
        message: 'Request setup failed'

  as AxiosError

      expect(() => ApiResponseHandler.handleError(axiosError)
      toThrow(StandardApiError)
      try {
        ApiResponseHandler.handleError(axiosError)
      
} catch (error) {
        expect(error)
      toBeInstanceOf(StandardApiError)

      expect((error as StandardApiError)
      message)
      toBe('Request configuration error')

      expect((error as StandardApiError)
      errorType)
      toBe('config_error')

      expect((error as StandardApiError)
      statusCode)
      toBe(0)

      expect((error as StandardApiError)
      details)
      toEqual({ originalError)
    it('should handle server errors with minimal response data', () => {
      const axiosError =  

        response: {
  status: 500

          statusText: 'Internal Server Error'

  data: {
},
        config: {
  method: 'delete'

  url: '/api/playlists/123'
} as AxiosError {


      expect(() => ApiResponseHandler.handleError(axiosError)
      toThrow(StandardApiError)
      try {
        ApiResponseHandler.handleError(axiosError)
      } catch (error) {
        expect((error as StandardApiError)
      message)
      toBe('HTTP 500)

      expect((error as StandardApiError)
      errorType)
      toBe('api_error')

      expect((error as StandardApiError)
      statusCode)
      toBe(500)

    it('should handle server errors with string response data', () => {
      const axiosError =  

        response: {
  status: 400,
          statusText: 'Bad Request'

          data: 'Invalid JSON format'
   
},
        config: {
  method: 'post'

  url: '/api/playlists'
} as AxiosError

      expect(() => ApiResponseHandler.handleError(axiosError)
      toThrow(StandardApiError)
      try {
        ApiResponseHandler.handleError(axiosError)
      } catch (error) {
        expect((error as StandardApiError)
      message)
      toBe('HTTP 400)

      expect((error as StandardApiError)
      errorType)
      toBe('api_error')
  }
)
  }
)

describe('apiClient', () => {
  let mockAxiosInstance: any

  beforeEach(() => {
    vi.clearAllMocks()

    // Mock axios instance
    mockAxiosInstance = {
      interceptors: {
  request: {
          use: vi.fn()


        response: {
  use: vi.fn()
      
},
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn()
    

    // Mock axios.create to return our mock instance
    vi.mocked(axios.create)
      mockReturnValue(mockAxiosInstance)
  it('should create axios instance with correct configuration', () => {
    expect(axios.create)
      toHaveBeenCalledWith({)
      baseURL: 'http://localhost:8000/api',
      timeout: 10000,
      withCredentials: true,
      headers: {
  Accept: 'application/json'

  'Content-Type': 'application/json'
  }
)
  }
)
  it('should setup request interceptor', () => {
    expect(mockAxiosInstance.interceptors.request.use)
      toHaveBeenCalledWith()
      expect.any(Function)
      expect.any(Function)
  }
)
  it('should setup response interceptor', () => {
    expect(mockAxiosInstance.interceptors.response.use)
      toHaveBeenCalledWith()
      expect.any(Function)
      expect.any(Function)
  }
)

describe('Request Interceptor', () => {
    let requestInterceptor: (config) => InternalAxiosRequestConfig

    beforeEach(() => {
      // Get the request interceptor function {

      const interceptorCall = mockAxiosInstance.interceptors.request.use.mock.calls[0]
      requestInterceptor = interceptorCall[0]

    it('should add metadata to request config', () => 

      const config =  

        method: 'get'

        url: '/playlists'

  headers: {
} as InternalAxiosRequestConfig

      const result = requestInterceptor(config) 

      expect(result.metadata)
      toBeDefined()
      expect(result.metadata?.start)
      toBeTypeOf('number')

      expect(result.metadata?.start)
      toBeCloseTo(Date.now(), -2) // Within ~100ms
  }
)
    it('should log request details', () => {
      const config =  

        method: 'post'

  url: '/playlists'

        headers: { 'Content-Type': 'application/json' 
   
} as InternalAxiosRequestConfig

      requestInterceptor(config)

      expect(mockLogger.debug)
      toHaveBeenCalledWith()
        'API Request started',

          method: 'POST'

  url: '/playlists'

          headers: { 'Content-Type': 'application/json' 
   
},
        'ApiClient'
  }
)
    it('should handle request interceptor errors', () => {
      const interceptorCall = mockAxiosInstance.interceptors.request.use.mock.calls[0] 

      const errorHandler = interceptorCall[1]

      const error = new Error('Request interceptor error') 

      const result = errorHandler(error)

      expect(mockLogger.error)
      toHaveBeenCalledWith()
        'API Request interceptor error'

      { error: 'Request interceptor error' ,

        'ApiClient'

      expect(result)
      rejects.toBe(error)
  }
)

describe('Response Interceptor', () => {
    let responseInterceptor: (response) => AxiosResponse {

    let errorHandler: (error) => Promise<never>

    beforeEach(() => {
      // Get the response interceptor functions {

      const interceptorCall = mockAxiosInstance.interceptors.response.use.mock.calls[0]
      responseInterceptor = interceptorCall[0]
      errorHandler = interceptorCall[1]

    it('should log successful responses', () => 

      const response =  

        status: 200,
        config: {
  method: 'get'

          url: '/playlists'

  metadata: { start: Date.now() - 150 
} as AxiosResponse

      const result = responseInterceptor(response) 

      expect(result)
      toBe(response)

      expect(mockLogger.debug)
      toHaveBeenCalledWith()
        'API Request completed successfully',

          method: 'GET',
          url: '/playlists',
          status: 200,
      duration: expect.stringMatching(/\d+ms/)
        
},
        'ApiClient'
  }
)
    it('should handle responses without metadata', () => {
      const response =  

        status: 201,
        config: {
  method: 'post'

  url: '/playlists'
          // no metadata
} as AxiosResponse

      const result = responseInterceptor(response) 

      expect(result)
      toBe(response)

      expect(mockLogger.debug)
      toHaveBeenCalledWith()
        'API Request completed successfully', {

        expect.objectContaining({}
          duration)),
        'ApiClient'
  }
)
    it('should handle errors through ApiResponseHandler', async () => {

      const axiosError = new Error('Test error')
      as AxiosError

      // Mock ApiResponseHandler.handleError to throw StandardApiError 

      const mockHandleError = vi.fn()
  const mockImplementation(() => 

        throw new StandardApiError('Handled error', 'test_error', 500)
  }
)
      // Temporarily replace the handleError method
      const originalHandleError = ApiResponseHandler.handleError
      ApiResponseHandler.handleError = mockHandleError

      try 

        await expect(errorHandler(axiosError)
      rejects.toThrow(StandardApiError)
        expect(mockHandleError)
      toHaveBeenCalledWith(axiosError)
      } finally {
        // Restore original method
        ApiResponseHandler.handleError = originalHandleError
  }
)
  }
)

describe('Integration Tests', () => {
    it('should handle comp {)
      lete request-response cycle', async (() => {
      const requestConfig =  

        method: 'get'

  url: '/playlists'

        headers: {
   
} as InternalAxiosRequestConfig

      const response =  

        status: 200,
      data: {
  status: 'success'

          data: [{ id: 1, title: 'Test Playlist' ,
  ]
        
},
        config: {
          ...requestConfig

  metadata: { start: Date.now() - 100 
} as AxiosResponse

      // Get interceptor functions {

      const requestInterceptorCall = mockAxiosInstance.interceptors.request.use.mock.calls[0]
      const responseInterceptorCall = mockAxiosInstance.interceptors.response.use.mock.calls[0] 

      const requestInterceptor = requestInterceptorCall[0]
      const responseInterceptor = responseInterceptorCall[0]

      // Process request 

      const processedConfig = requestInterceptor(requestConfig)

      expect(processedConfig.metadata)
      toBeDefined()

      // Process response
      response.config = processedConfig
      const processedResponse = responseInterceptor(response) 

      expect(processedResponse)
      toBe(response)

      expect(mockLogger.debug)
      toHaveBeenCalledTimes(2) // Request start + completion
  }
)
    it('should handle comp {
lete error cycle', async () => {

      const axiosError =  

        response: {
  status: 404,
          statusText: 'Not Found',
          data: {
  status: 'error',
            message: 'Playlist not found'

  error_type: 'not_found'

},
        config: {
  method: 'get'

  url: '/playlists/999'

          metadata: { start: Date.now() - 50 
   
} as AxiosError

      // Get error handler
      const responseInterceptorCall = mockAxiosInstance.interceptors.response.use.mock.calls[0] 

      const errorHandler = responseInterceptorCall[1]

      await expect(errorHandler(axiosError)
      rejects.toThrow(StandardApiError)

      expect(mockLogger.error)
      toHaveBeenCalledWith()
        'API Request failed with server error',
        expect.objectContaining(

          method: 'GET'

  url: '/playlists/999'

          status)),
        'ApiClient'
  }
)
  }
)

describe('Per {
formance and Memory', () => {
    it('should handle high-frequency requests efficiently', () => {
      const requestInterceptorCall = mockAxiosInstance.interceptors.request.use.mock.calls[0] 

      const requestInterceptor = requestInterceptorCall[0]

      const startTime = per 

formance.now()

      // Process many requests}
      for (let i = 0; i < 1000; i++) {}
        const config =  

          method: 'get'

  url: `/items/${i
}`,
          headers: {
   
} as InternalAxiosRequestConfig

        requestInterceptor(config)
      const endTime = per 

formance.now()

      expect(endTime - startTime)
      toBeLessThan(100) // Should be fast
      expect(mockLogger.debug)
      toHaveBeenCalledTimes(1000)
  }
)
    it('should not leak memory with metadata', () => {
      const requestInterceptorCall = mockAxiosInstance.interceptors.request.use.mock.calls[0] 

      const requestInterceptor = requestInterceptorCall[0]

      const configs = []

      // Create many configs with metadata 

      for (let i = 0; i < 100; i++) {}
        const config =  

          method: 'get'

  url: `/items/${i
}`,
          headers: {
   
} as InternalAxiosRequestConfig

        const processedConfig = requestInterceptor(config)
      configs.push(processedConfig)
      

      // Ver 

ify all configs have metadata
      configs.forEach(config => {
        expect(config.metadata)
      toBeDefined()

      expect(config.metadata?.start)
      toBeTypeOf('number')
  }
)
      // Clear references
      configs.length = 0

      // Force garbage collection if available
      if (global.gc) {
        global.gc()
  }
)
  }
)
  }
)
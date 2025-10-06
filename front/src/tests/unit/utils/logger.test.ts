/**
 * Unit tests for logger.ts
 *
 * Tests the frontend logging utility including:
 * - Log level management and filtering
 * - Environment-based configuration
 * - Message formatting and timestamping
 * - Console output delegation
 * - Context handling and structured logging
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Mock process.env before importing logger
const originalNodeEnv = process.env.NODE_ENV

// Mock console methods
const originalConsole = {
  error: console.error,
  warn: console.warn,
  info: console.info,
  log: console.log
}

describe('logger', () => {
  beforeEach(() => {
    // Mock console methods
    console.error = vi.fn()
  })

  console.warn = vi.fn()
    console.info = vi.fn()
    console.log = vi.fn()

    // Clear module cache to test fresh logger instances
    vi.resetModules()
  })

  afterEach(() => {
    // Restore console methods
    console.error = originalConsole.error
    console.warn = originalConsole.warn
    console.info = originalConsole.info
    console.log = originalConsole.log

    // Restore NODE_ENV
    process.env.NODE_ENV = originalNodeEnv
  })

  describe('Environment Configuration', () => {
    it('should configure DEBUG level in development environment', async () => {
      process.env.NODE_ENV = 'development'

      const { logger } = await import('@/utils/logger')
      logger.debug('Test debug message')
      logger.info('Test info message')
      logger.warn('Test warn message')
      logger.error('Test error message')

      expect(console.log).toHaveBeenCalled() // DEBUG
      expect(console.info).toHaveBeenCalled() // INFO
      expect(console.warn).toHaveBeenCalled() // WARN
      expect(console.error).toHaveBeenCalled() // ERROR
    })

    it('should configure WARN level in production environment', async () => {
      process.env.NODE_ENV = 'production'

      const { logger } = await import('@/utils/logger')
      logger.debug('Test debug message')
      logger.info('Test info message')
      logger.warn('Test warn message')
      logger.error('Test error message')

      expect(console.log).not.toHaveBeenCalled() // DEBUG filtered
      expect(console.info).not.toHaveBeenCalled() // INFO filtered
      expect(console.warn).toHaveBeenCalled() // WARN allowed
      expect(console.error).toHaveBeenCalled() // ERROR allowed
    })

    it('should configure WARN level in test environment', async () => {
      process.env.NODE_ENV = 'test'

      const { logger } = await import('@/utils/logger')
      logger.debug('Test debug message')
      logger.info('Test info message')
      logger.warn('Test warn message')
      logger.error('Test error message')

      expect(console.log).not.toHaveBeenCalled() // DEBUG filtered
      expect(console.info).not.toHaveBeenCalled() // INFO filtered
      expect(console.warn).toHaveBeenCalled() // WARN allowed
      expect(console.error).toHaveBeenCalled() // ERROR allowed
    })

    it('should default to WARN level for unknown environments', async () => {
      process.env.NODE_ENV = 'staging'

      const { logger } = await import('@/utils/logger')
      logger.debug('Test debug message')
      logger.info('Test info message')
      logger.warn('Test warn message')
      logger.error('Test error message')

      expect(console.log).not.toHaveBeenCalled() // DEBUG filtered
      expect(console.info).not.toHaveBeenCalled() // INFO filtered
      expect(console.warn).toHaveBeenCalled() // WARN allowed
      expect(console.error).toHaveBeenCalled() // ERROR allowed
    })
  })

  describe('Log Level Filtering', () => {
    it('should filter logs based on current level', async () => {
      process.env.NODE_ENV = 'production' // WARN level

      const { logger } = await import('@/utils/logger')

      // Only WARN and ERROR should be logged
      logger.debug('Debug message')
      logger.info('Info message')
      logger.warn('Warn message')
      logger.error('Error message')

      expect(console.log).not.toHaveBeenCalled()
      expect(console.info).not.toHaveBeenCalled()
      expect(console.warn).toHaveBeenCalledTimes(1)
      expect(console.error).toHaveBeenCalledTimes(1)
    })

    it('should log all levels in development', async () => {
      process.env.NODE_ENV = 'development' // DEBUG level

      const { logger } = await import('@/utils/logger')
      logger.debug('Debug message')
      logger.info('Info message')
      logger.warn('Warn message')
      logger.error('Error message')

      expect(console.log).toHaveBeenCalledTimes(1)
      expect(console.info).toHaveBeenCalledTimes(1)
      expect(console.warn).toHaveBeenCalledTimes(1)
      expect(console.error).toHaveBeenCalledTimes(1)
    })
  })

  describe('Message Formatting', () => {
    it('should format messages with timestamp and level', async () => {
      process.env.NODE_ENV = 'development'

      const { logger } = await import('@/utils/logger')
      logger.error('Test error message')

      expect(console.error).toHaveBeenCalledWith(
        expect.stringMatching(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z ERROR Test error message$/)
      )
    })

    it('should include context in formatted message', async () => {
      process.env.NODE_ENV = 'development'

      const { logger } = await import('@/utils/logger')
      logger.info('Test message', undefined, 'TestContext')

      expect(console.info).toHaveBeenCalledWith(
        expect.stringMatching(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z INFO \[TestContext\] Test message$/)
      )
    })

    it('should format message without context when not provided', async () => {
      process.env.NODE_ENV = 'development'

      const { logger } = await import('@/utils/logger')
      logger.warn('Test warning')

      expect(console.warn).toHaveBeenCalledWith(
        expect.stringMatching(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z WARN Test warning$/)
      )
    })
  })

  describe('Data Handling', () => {
    it('should log message with data object', async () => {
      process.env.NODE_ENV = 'development'

      const { logger } = await import('@/utils/logger')
      const testData = { user: 'john', action: 'login', timestamp: 123456 }
      logger.info('User action', testData)

      expect(console.info).toHaveBeenCalledWith(
        expect.stringMatching(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z INFO User action$/),
        testData
      )
    })

    it('should log message without data when data is undefined', async () => {
      process.env.NODE_ENV = 'development'

      const { logger } = await import('@/utils/logger')
      logger.error('Error message', undefined)

      expect(console.error).toHaveBeenCalledWith(
        expect.stringMatching(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z ERROR Error message$/)
      )
      expect(console.error).toHaveBeenCalledTimes(1)
    })
  })

  describe('Export Structure', () => {
    it('should export logger as named export', async () => {
      const { logger } = await import('@/utils/logger')
      expect(logger).toBeDefined()
      expect(typeof logger.error).toBe('function')
      expect(typeof logger.warn).toBe('function')
      expect(typeof logger.info).toBe('function')
      expect(typeof logger.debug).toBe('function')
    })
  })

  describe('Edge Cases and Error Handling', () => {
    it('should handle empty messages', async () => {
      process.env.NODE_ENV = 'development'

      const { logger } = await import('@/utils/logger')
      logger.info('')
      logger.debug('')

      expect(console.info).toHaveBeenCalledWith(
        expect.stringMatching(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z INFO $/)
      )
      expect(console.log).toHaveBeenCalledWith(
        expect.stringMatching(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z DEBUG $/)
      )
    })

    it('should handle undefined NODE_ENV', async () => {
      delete process.env.NODE_ENV

      const { logger } = await import('@/utils/logger')
      logger.debug('Debug message')
      logger.info('Info message')
      logger.warn('Warn message')

      // Should default to WARN level when NODE_ENV is undefined
      expect(console.log).not.toHaveBeenCalled() // DEBUG filtered
      expect(console.info).not.toHaveBeenCalled() // INFO filtered
      expect(console.warn).toHaveBeenCalled() // WARN allowed
    })
  })
})
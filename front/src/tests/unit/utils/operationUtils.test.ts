/**
 * Unit tests for operationUtils.ts
 *
 * Tests the centralized operation ID utilities including:
 * - Client operation ID generation with uniqueness
 * - Operation ID validation and format checking
 * - Operation name extraction and parsing
 * - Edge cases and error handling
 * - Performance with high-frequency generation
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  generateClientOpId,
  validateClientOpId,
  extractOperationName
} from '@/utils/operationUtils'

describe('operationUtils', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('generateClientOpId', () => {
    it('should generate operation ID with correct format', () => {
      const operation = 'create_playlist'

      const clientOpId = generateClientOpId(operation)

      expect(clientOpId)
        .toMatch(/^create_playlist_\d+_[a-z0-9]{9}$/)
    })

    it('should include operation name in generated ID', () => {
      const operations = ['delete_track', 'update_playlist', 'upload_file']

      operations.forEach(operation => {
        const clientOpId = generateClientOpId(operation)
        expect(clientOpId)
          .toMatch(new RegExp(`^${operation.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}_`))
      })
    })

    it('should include timestamp in generated ID', () => {
      const mockTimestamp = 1642234567890

      const dateSpy = vi.spyOn(Date, 'now')
        .mockReturnValue(mockTimestamp)
      const clientOpId = generateClientOpId('test_operation')

      expect(clientOpId)
        .toContain(`_${mockTimestamp}_`)
      dateSpy.mockRestore()
    })

    it('should include random suffix in generated ID', () => {
      const mockRandom = 0.123456789

      const mathSpy = vi.spyOn(Math, 'random')
        .mockReturnValue(mockRandom)
      const clientOpId = generateClientOpId('test_operation')

      // Math.random().toString(36).substr(2, 9) for 0.123456789 should be "4fzyo82oa"
      expect(clientOpId)
        .toMatch(/_[a-z0-9]{9}$/)
      mathSpy.mockRestore()
    })

    it('should generate unique IDs for same operation', () => {
      const operation = 'test_operation'

      const ids = new Set()

      // Generate 1000 IDs and check uniqueness
      for (let i = 0; i < 1000; i++) {
        const id = generateClientOpId(operation)
        expect(ids.has(id)).toBe(false)
        ids.add(id)
      }
      expect(ids.size).toBe(1000)
    })

    it('should handle operations with underscores', () => {
      const operation = 'complex_operation_with_many_parts'

      const clientOpId = generateClientOpId(operation)
      expect(clientOpId)
        .toMatch(new RegExp(`^${operation.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}_`))

      expect(validateClientOpId(clientOpId)).toBe(true)
    })

    it('should handle single word operations', () => {
      const operation = 'play'

      const clientOpId = generateClientOpId(operation)
      expect(clientOpId)
        .toMatch(new RegExp(`^${operation}_`))

      expect(validateClientOpId(clientOpId)).toBe(true)
    })

    it('should handle empty operation name', () => {
      const operation = ''

      const clientOpId = generateClientOpId(operation)
      expect(clientOpId)
        .toMatch(/^_\d+_[a-z0-9]{9}$/)

      expect(validateClientOpId(clientOpId)).toBe(true)
    })

    it('should handle special characters in operation name', () => {
      const operation = 'test-operation.with@special#chars'

      const clientOpId = generateClientOpId(operation)
      expect(clientOpId)
        .toMatch(new RegExp(`^${operation.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}_`))

      expect(clientOpId)
        .toMatch(/_\d+_[a-z0-9]{9}$/)
    })

    it('should be performant for high-frequency generation', () => {
      const startTime = performance.now()

      // Generate many IDs rapidly
      for (let i = 0; i < 10000; i++) {
        generateClientOpId('performance_test')
      }
      const endTime = performance.now()

      expect(endTime - startTime)
        .toBeLessThan(1000) // Should complete within 1 second
    })
  })

  describe('validateClientOpId', () => {
    it('should validate correctly formatted operation IDs', () => {
      const validIds = [
        'create_playlist_1642234567890_abc123def',
        'delete_track_1234567890_xyz789ghi',
        'upload_file_9876543210_mno456pqr',
        'play_1000000000_a1b2c3d4e'
      ]

      validIds.forEach(id => {
        expect(validateClientOpId(id))
          .toBe(true)
      })
    })

    it('should reject null or undefined IDs', () => {
      expect(validateClientOpId(null as any))
        .toBe(false)
      expect(validateClientOpId(undefined as any))
        .toBe(false)
    })

    it('should reject non-string IDs', () => {
      expect(validateClientOpId(123 as any))
        .toBe(false)
      expect(validateClientOpId({} as any))
        .toBe(false)
      expect(validateClientOpId([] as any))
        .toBe(false)
      expect(validateClientOpId(true as any))
        .toBe(false)
    })

    it('should reject empty strings', () => {
      expect(validateClientOpId(''))
        .toBe(false)
    })

    it('should reject IDs with insufficient parts', () => {
      const invalidIds = [
        'single_part',
        'two_parts',
        'operation_timestamp', // Only 2 parts
        'operation__suffix' // Empty timestamp
      ]

      invalidIds.forEach(id => {
        expect(validateClientOpId(id))
          .toBe(false)
      })
    })

    it('should reject IDs with non-numeric timestamp', () => {
      const invalidIds = [
        'operation_not_a_number_suffix',
        'operation_abc123_suffix',
        'operation__suffix', // Empty timestamp
        'operation_12ab34_suffix' // Mixed alphanumeric
      ]

      invalidIds.forEach(id => {
        expect(validateClientOpId(id))
          .toBe(false)
      })
    })

    it('should validate IDs with extra underscores in operation name', () => {
      const complexOpId = 'complex_operation_with_many_parts_1642234567890_abc123def'

      expect(validateClientOpId(complexOpId))
        .toBe(true)
    })

    it('should validate IDs with empty operation name', () => {
      const emptyOpId = '_1642234567890_abc123def'

      expect(validateClientOpId(emptyOpId))
        .toBe(true)
    })

    it('should handle very long operation IDs', () => {
      const longOperation = 'a'.repeat(1000)

      const longOpId = `${longOperation}_1642234567890_abc123def`
      expect(validateClientOpId(longOpId))
        .toBe(true)
    })

    it('should reject malformed IDs with special cases', () => {
      const malformedIds = [
        'operation_1234_', // Missing suffix
        'operation__suffix', // Empty timestamp
        'operation_1234_' // Missing suffix
      ]

      // Note: Some of these might actually be valid depending on implementation
      expect(validateClientOpId('operation_1234_'))
        .toBe(false) // Missing suffix
      expect(validateClientOpId('operation__suffix'))
        .toBe(false) // Empty timestamp
    })

    it('should be performant for high-frequency validation', () => {
      const validId = 'test_operation_1642234567890_abc123def'

      const startTime = performance.now()

      // Validate many IDs rapidly
      for (let i = 0; i < 10000; i++) {
        validateClientOpId(validId)
      }
      const endTime = performance.now()

      expect(endTime - startTime)
        .toBeLessThan(100) // Should be very fast
    })
  })

  describe('extractOperationName', () => {
    it('should extract operation name from valid IDs', () => {
      const testCases = [
        { id: 'create_playlist_1642234567890_abc123def', expected: 'create_playlist' },
        { id: 'delete_track_1234567890_xyz789ghi', expected: 'delete_track' },
        { id: 'play_9876543210_mno456pqr', expected: 'play' },
        { id: 'complex_operation_name_1000000000_a1b2c3d4e', expected: 'complex_operation_name' }
      ]

      testCases.forEach(({ id, expected }) => {
        expect(extractOperationName(id))
          .toBe(expected)
      })
    })

    it('should return null for invalid IDs', () => {
      const invalidIds = [
        null,
        undefined,
        '',
        'invalid_format',
        'two_parts',
        'operation_not_numeric_suffix',
        123,
        {}
      ]

      invalidIds.forEach(id => {
        expect(extractOperationName(id as any))
          .toBeNull()
      })
    })

    it('should handle empty operation name', () => {
      const emptyOpId = '_1642234567890_abc123def'

      expect(extractOperationName(emptyOpId))
        .toBe('')
    })

    it('should handle operation names with multiple underscores', () => {
      const complexOpId = 'very_complex_operation_with_many_underscores_1642234567890_abc123def'

      expect(extractOperationName(complexOpId))
        .toBe('very_complex_operation_with_many_underscores')
    })

    it('should handle special characters in operation name', () => {
      const specialOpId = 'test-operation.with@special#chars_1642234567890_abc123def'

      expect(extractOperationName(specialOpId))
        .toBe('test-operation.with@special#chars')
    })

    it('should be consistent with generateClientOpId', () => {
      const operations = [
        'create_playlist',
        'delete_track',
        'upload_file',
        'complex_operation_name',
        'play',
        ''
      ]

      operations.forEach(operation => {
        const generatedId = generateClientOpId(operation)
        const extractedName = extractOperationName(generatedId)
        expect(extractedName)
          .toBe(operation)
      })
    })

    it('should be performant for high-frequency extraction', () => {
      const validId = 'test_operation_1642234567890_abc123def'

      const startTime = performance.now()

      // Extract many operation names rapidly
      for (let i = 0; i < 10000; i++) {
        extractOperationName(validId)
      }
      const endTime = performance.now()

      expect(endTime - startTime)
        .toBeLessThan(100) // Should be very fast
    })
  })

  describe('Integration Tests', () => {
    it('should work correctly in complete workflow', () => {
      const operation = 'integration_test'

      // Generate ID
      const clientOpId = generateClientOpId(operation)

      // Validate ID
      expect(validateClientOpId(clientOpId)).toBe(true)

      // Extract operation name
      const extractedName = extractOperationName(clientOpId)
      expect(extractedName)
        .toBe(operation)
    })

    it('should handle batch operations', () => {
      const operations = [
        'create_playlist',
        'add_track',
        'delete_track',
        'update_metadata',
        'reorder_tracks'
      ]

      const generatedIds = operations.map(op => generateClientOpId(op))

      // All IDs should be unique
      const uniqueIds = new Set(generatedIds)
      expect(uniqueIds.size)
        .toBe(operations.length)

      // All IDs should be valid
      generatedIds.forEach(id => {
        expect(validateClientOpId(id))
          .toBe(true)
      })

      // Should extract correct operation names
      generatedIds.forEach((id, index) => {
        expect(extractOperationName(id))
          .toBe(operations[index])
      })
    })

    it('should maintain consistency across time', () => {
      const operation = 'time_test'

      const ids = []

      // Generate IDs with small delays
      for (let i = 0; i < 10; i++) {
        ids.push(generateClientOpId(operation))
        // Small delay to ensure different timestamps
        if (i < 9) {
          const start = Date.now()
          while (Date.now() - start < 1) {
            // Busy wait for 1ms
          }
      }

      // All should be unique (different timestamps)
      const uniqueIds = new Set(ids)
      expect(uniqueIds.size)
        .toBe(10)

      // All should be valid and extract to same operation
      ids.forEach(id => {
        expect(validateClientOpId(id))
          .toBe(true)
        expect(extractOperationName(id))
          .toBe(operation)
      })
    })
  })

  describe('Edge Cases and Robustness', () => {
    it('should handle extreme timestamp values', () => {
      const mockTimestamp = Number.MAX_SAFE_INTEGER

      const dateSpy = vi.spyOn(Date, 'now')
        .mockReturnValue(mockTimestamp)
      const clientOpId = generateClientOpId('extreme_test')

      expect(validateClientOpId(clientOpId)).toBe(true)
      expect(extractOperationName(clientOpId))
        .toBe('extreme_test')

      dateSpy.mockRestore()
    })

    it('should handle zero timestamp', () => {
      const dateSpy = vi.spyOn(Date, 'now')
        .mockReturnValue(0)

      const clientOpId = generateClientOpId('zero_test')

      expect(validateClientOpId(clientOpId)).toBe(true)
      expect(extractOperationName(clientOpId))
        .toBe('zero_test')

      dateSpy.mockRestore()
    })

    it('should handle very long operation names', () => {
      const longOperation = 'very_long_operation_name_'.repeat(100)

      const clientOpId = generateClientOpId(longOperation)

      expect(validateClientOpId(clientOpId)).toBe(true)
      expect(extractOperationName(clientOpId))
        .toBe(longOperation)
    })

    it('should handle operation names that look like timestamps', () => {
      const trickyCases = [
        '1234567890',
        '1234567890_operation',
        'operation_1234567890'
      ]

      trickyCases.forEach(operation => {
        const clientOpId = generateClientOpId(operation)
        expect(validateClientOpId(clientOpId)).toBe(true)
        expect(extractOperationName(clientOpId))
          .toBe(operation)
      })
    })

    it('should handle Unicode characters in operation names', () => {
      const unicodeOperations = [
        'créer_playlist',
        'операция_тест',
        '操作_测试',
        'opération_🎵_test'
      ]

      unicodeOperations.forEach(operation => {
        const clientOpId = generateClientOpId(operation)
        expect(validateClientOpId(clientOpId)).toBe(true)
        expect(extractOperationName(clientOpId))
          .toBe(operation)
      })
    })

    it('should handle random suffix edge cases', () => {
      // Test with Math.random() returning edge values
      const mathSpy = vi.spyOn(Math, 'random')

      // Test with 0 (minimum)
      mathSpy.mockReturnValue(0)
      let clientOpId = generateClientOpId('edge_test')
      expect(validateClientOpId(clientOpId)).toBe(true)

      // Test with value close to 1 (maximum)
      mathSpy.mockReturnValue(0.9999999999)
      clientOpId = generateClientOpId('edge_test')
      expect(validateClientOpId(clientOpId)).toBe(true)

      mathSpy.mockRestore()
    })
  })

  describe('Memory and Performance', () => {
    it('should not leak memory with frequent operations', () => {
      const operations = []

      // Generate many operation IDs
      for (let i = 0; i < 10000; i++) {
        const operation = `test_${i % 100}` // Reuse operation names
        const id = generateClientOpId(operation)

        // Only keep every 1000th ID to avoid memory issues in test
        if (i % 1000 === 0) {
          operations.push(id)
        }

      // Verify some operations
      operations.forEach(id => {
        expect(validateClientOpId(id))
          .toBe(true)
      })

      // Force garbage collection if available
      if (global.gc) {
        global.gc()
      })

    it('should maintain performance with concurrent operations', () => {
      const results = []

      const startTime = performance.now()

      // Simulate concurrent operation ID generation
      for (let i = 0; i < 1000; i++) {
        const promises = Array.from({ length: 10 }, (_, j) => {
          return Promise.resolve(generateClientOpId(`concurrent_${i}_${j}`))
        })
        results.push(...promises)
      }

      const endTime = performance.now()

      expect(endTime - startTime)
        .toBeLessThan(500) // Should be fast
      expect(results.length)
        .toBe(10000)
    })
  })
})

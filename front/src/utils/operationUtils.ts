/**
 * Centralized utility for generating client operation IDs
 * Eliminates duplication across API service methods
 */

/**
 * Generates a unique client operation ID for request tracking and deduplication
 * @param operation - The operation name (e.g., 'create_playlist', 'delete_track')
 * @returns A unique operation ID string
 */
export function generateClientOpId(operation: string): string {
  const timestamp = Date.now()
  const randomSuffix = Math.random().toString(36).substr(2, 9)
  return `${operation}_${timestamp}_${randomSuffix}`
}

/**
 * Validates a client operation ID format
 * @param clientOpId - The operation ID to validate
 * @returns True if valid, false otherwise
 */
export function validateClientOpId(clientOpId: string): boolean {
  if (!clientOpId || typeof clientOpId !== 'string') {
    return false
  }
  
  // Should match pattern: operation_timestamp_random
  const parts = clientOpId.split('_')
  return parts.length >= 3 && parts[1].length > 0 && !isNaN(Number(parts[1]))
}

/**
 * Extracts the operation name from a client operation ID
 * @param clientOpId - The operation ID
 * @returns The operation name or null if invalid
 */
export function extractOperationName(clientOpId: string): string | null {
  if (!validateClientOpId(clientOpId)) {
    return null
  }
  
  const parts = clientOpId.split('_')
  return parts[0]
}
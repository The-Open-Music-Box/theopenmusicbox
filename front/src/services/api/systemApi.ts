/**
 * System API Module
 * Handles system-related operations
 */

import { apiClient, ApiResponseHandler } from './apiClient'
import { API_ROUTES } from '../../constants/apiRoutes'
import { ApiResponse } from '../../types/contracts'

/**
 * System API methods with standardized response handling
 */
export const systemApi = {
  /**
   * Get system health
   */
  async getHealth(): Promise<{ status: string; uptime: number }> {
    const response = await apiClient.get<ApiResponse<{ status: string; uptime: number }>>(
      API_ROUTES.HEALTH
    )
    return ApiResponseHandler.extractData(response)
  },

  /**
   * Get system volume
   */
  async getVolume(): Promise<{ volume: number; muted: boolean }> {
    const response = await apiClient.get<ApiResponse<{ volume: number; muted: boolean }>>(
      API_ROUTES.VOLUME
    )
    return ApiResponseHandler.extractData(response)
  }
}
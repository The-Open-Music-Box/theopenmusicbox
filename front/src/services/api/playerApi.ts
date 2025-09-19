/**
 * Player API Module
 * Handles all audio player related operations
 */

import { apiClient, ApiResponseHandler } from './apiClient'
import { API_ROUTES } from '../../constants/apiRoutes'
import { generateClientOpId } from '../../utils/operationUtils'
import { ApiResponse, PlayerState } from '../../types/contracts'

/**
 * Player API methods with standardized response handling
 */
export const playerApi = {
  /**
   * Get current player status
   */
  async getStatus(): Promise<PlayerState> {
    const response = await apiClient.get<ApiResponse<PlayerState>>(API_ROUTES.PLAYER_STATUS)
    return response.data.data!
  },

  /**
   * Stop playback
   */
  async stop(clientOpId?: string): Promise<PlayerState> {
    const response = await apiClient.post<ApiResponse<PlayerState>>(
      API_ROUTES.PLAYER_STOP,
      { client_op_id: clientOpId || generateClientOpId('api_operation') }
    )
    return response.data.data!
  },

  /**
   * Skip to next track
   */
  async next(clientOpId?: string): Promise<PlayerState> {
    const response = await apiClient.post<ApiResponse<PlayerState>>(
      API_ROUTES.PLAYER_NEXT,
      { client_op_id: clientOpId || generateClientOpId('api_operation') }
    )
    return response.data.data!
  },

  /**
   * Skip to previous track
   */
  async previous(clientOpId?: string): Promise<PlayerState> {
    const response = await apiClient.post<ApiResponse<PlayerState>>(
      API_ROUTES.PLAYER_PREVIOUS,
      { client_op_id: clientOpId || generateClientOpId('api_operation') }
    )
    return response.data.data!
  },

  /**
   * Toggle play/pause
   */
  async toggle(clientOpId?: string): Promise<PlayerState> {
    const response = await apiClient.post<ApiResponse<PlayerState>>(
      API_ROUTES.PLAYER_TOGGLE,
      { client_op_id: clientOpId || generateClientOpId('api_operation') }
    )
    return response.data.data!
  },

  /**
   * Seek to position
   */
  async seek(positionMs: number, clientOpId?: string): Promise<PlayerState> {
    const payload = {
      position_ms: positionMs,
      client_op_id: clientOpId || generateClientOpId('api_operation')
    }

    const response = await apiClient.post<ApiResponse<PlayerState>>(
      API_ROUTES.PLAYER_SEEK,
      payload
    )
    return response.data.data!
  },

  /**
   * Set volume
   */
  async setVolume(volume: number, clientOpId?: string): Promise<PlayerState> {
    const response = await apiClient.post<ApiResponse<PlayerState>>(
      API_ROUTES.VOLUME,
      {
        volume,
        client_op_id: clientOpId || generateClientOpId('api_operation')
      }
    )
    return response.data.data!
  }
}
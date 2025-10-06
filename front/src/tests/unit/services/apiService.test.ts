/**
 * Unit tests for apiService.ts
 *
 * Tests the main API service orchestration including:
 * - Modular API organization and delegation
 * - Backward compatibility methods
 * - Error handling and type checking
 * - Integration with specialized API modules
 * - Response format handling and fallbacks
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { apiService, StandardApiError } from '@/services/apiService'
import { flushPromises } from '@/tests/utils/testHelpers'

// Mock all API modules
const mockPlayerApi = {
  getStatus: vi.fn(),
  toggle: vi.fn(),
  seek: vi.fn(),
  previous: vi.fn(),
  next: vi.fn()
}

const mockPlaylistApi = {
  getPlaylists: vi.fn(),
  getPlaylist: vi.fn(),
  createPlaylist: vi.fn(),
  updatePlaylist: vi.fn(),
  deletePlaylist: vi.fn(),
  deleteTrack: vi.fn(),
  startPlaylist: vi.fn()
}

const mockUploadApi = {
  initUpload: vi.fn(),
  uploadChunk: vi.fn(),
  finalizeUpload: vi.fn(),
  getUploadStatus: vi.fn()
  }

  const mockSystemApi = {
  getSystemInfo: vi.fn(),    getHealth: vi.fn()
  }

  const mockNfcApi = {
  startNfcAssociationScan: vi.fn(),
  startNfcScan: vi.fn(),
  getNfcStatus: vi.fn(),
  associateNfcTag: vi.fn(),
  removeNfcAssociation: vi.fn()
}

const mockYoutubeApi = {
  downloadTrack: vi.fn(),
  getVideoInfo: vi.fn()
}

const mockApiClient = {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    deleteMethod: vi.fn()
}

const mockApiResponseHandler = {
  extractData: vi.fn()
}


// Mock API modules
vi.mock('@/services/api/playerApi', () => ({
  playerApi: vi.fn()
  }
)
vi.mock('@/services/api/playlistApi', () => ({
  playlistApi)
vi.mock('@/services/api/uploadApi', () => ({
  uploadApi)
vi.mock('@/services/api/systemApi', () => ({
  systemApi)
vi.mock('@/services/api/nfcApi', () => ({
  nfcApi)
vi.mock('@/services/api/youtubeApi', () => ({
  youtubeApi
  }
)
vi.mock('@/services/api/apiClient', () => ({
  apiClient: mockApiClient,
  ApiResponseHandler: mockApiResponseHandler

  StandardApiError: class MockStandardApiError extends Error {,
  constructor(
      public message: string,
      public errorType: string,
      public statusCode: number,
      public details?: any,
      public requestId?) {
      super(message)
      this.name = 'StandardApiError'

    isType(type) { return this.errorType === type ,
  isRetryable() { return this.statusCode >= 500 || this.errorType === 'rate_limit_exceeded'
  }
)

// Mock constants
vi.mock('@/ { constants/apiRoutes', () => ({
  API_ROUTES: {,
  PLAYLISTS: '/api/playlists',
  PLAYLIST_REORDER: (id) => `/api/playlists/${id
 }/reorder`,
    PLAYLIST_PLAY_TRACK: (id: string, trackNum) => `/api/playlists/${id,
  /play/${trackNum
}`,
    PLAYLIST_MOVE_TRACK: '/api/playlists/move-track',
  API_CONFIG: {,
  PLAYLISTS_FETCH_LIMIT: 50
  }
)

// Mock logger
vi.mock('@/utils/logger', () => ({
  logger: {,
  info),
    error: vi.fn(),
    debug: vi.fn()))
  const warn: vi.fn()

// Mock operation utils
vi.mock('@/utils/operationUtils', () => ({
  generateClientOpId) => 'test-op-id-123'
  }
)
  }
)

describe('apiService', () => {
  beforeEach(() => {
    vi.clearAllMocks()

    // Setup default successful responses}
    mockPlayerApi.getStatus.mockResolvedValue({ is_playing)
      mockPlayerApi.toggle.mockResolvedValue({ success)
      mockPlaylistApi.getPlaylists.mockResolvedValue({
      items: [{ id: '1', title: 'Test Playlist' ,
  ],
      total: 1,
      page: 1,
      limit)
      mockApiResponseHandler.extractData.mockImplementation((response) => response.data)
  }
)
  afterEach(() => {
    vi.clearAllMocks()
  }
)

describe('Service Organization', () => {
    it('should expose all API modules', () => {
      expect(apiService.player)
      toBeDefined()
      expect(apiService.playlists)
      toBeDefined()

      expect(apiService.uploads)
      toBeDefined()
      expect(apiService.system)
      toBeDefined()

      expect(apiService.nfc)
      toBeDefined()

      expect(apiService.youtube)
      toBeDefined()
  }
)
    it('should expose API client  for direct access', () => {
      expect(apiService.client)
      toBeDefined()
  }
)
    it('should expose error handling utilities', () => {
      expect(apiService.StandardApiError)
      toBeDefined()
      expect(apiService.isErrorType)
      toBeDefined()

      expect(apiService.isRetryable)
      toBeDefined()
  }
)
  }
)

describe('Error Handling Utilities', () => {
    it('should check error types correctly', () => {
      const apiError = new StandardApiError('Test error', 'validation_error', 400) {

      const genericError = new Error('Generic error')

      expect(apiService.isErrorType(apiError, 'validation_error')
      toBe(true)
      expect(apiService.isErrorType(apiError, 'network_error')
      toBe(false)
      expect(apiService.isErrorType(genericError, 'validation_error')
      toBe(false)
  }
)
    it('should check  if errors are retryable', () => {
      const serverError = new StandardApiError('Server error', 'internal_error', 500) {

      const rateLimitError = new StandardApiError('Rate limit', 'rate_limit_exceeded', 429)
      const clientError = new StandardApiError('Bad request', 'validation_error', 400) {

      const genericError = new Error('Generic error')

      expect(apiService.isRetryable(serverError)
      toBe(true)
      expect(apiService.isRetryable(rateLimitError)
      toBe(true)
      expect(apiService.isRetryable(clientError)
      toBe(false)
      expect(apiService.isRetryable(genericError)
      toBe(false)
  }
)
  }
)

describe('Player API Integration', () => {
    it('should delegate getPlayerStatus to playerApi', async () => {
      const mockStatus = { is_playing: true, volume: 75 ,
  mockPlayerApi.getStatus.mockResolvedValue(mockStatus)
      const result = {
 await apiService.getPlayerStatus()
      expect(mockPlayerApi.getStatus)
      toHaveBeenCalled()

      expect(result)
      toEqual(mockStatus)
  }
)
    it('should delegate togglePlayer to playerApi', async () => {

      const clientOpId = 'test-toggle-123'

      mockPlayerApi.toggle.mockResolvedValue({ success)
      const result = {
 await apiService.togglePlayer(clientOpId)
      expect(mockPlayerApi.toggle)
      toHaveBeenCalledWith(clientOpId)

      expect(result)
      toEqual({ success)
    it('should delegate playPlayer to playerApi toggle', async () => {
      mockPlayerApi.toggle.mockResolvedValue({ success)
      const result = {
 await apiService.playPlayer('play-op-123')
      expect(mockPlayerApi.toggle)
      toHaveBeenCalledWith('play-op-123')

      expect(result)
      toEqual({ success)
    it('should delegate pausePlayer to playerApi toggle', async () => {
      mockPlayerApi.toggle.mockResolvedValue({ success)
      const result = {
 await apiService.pausePlayer('pause-op-123')
      expect(mockPlayerApi.toggle)
      toHaveBeenCalledWith('pause-op-123')

      expect(result)
      toEqual({ success)
    it('should delegate seekPlayer to playerApi', async () => {
      const positionMs = 30000 }
      const clientOpId = 'seek-op-123'}
      mockPlayerApi.seek.mockResolvedValue({ success)
      const result = {
 await apiService.seekPlayer(positionMs, clientOpId)
      expect(mockPlayerApi.seek)
      toHaveBeenCalledWith(positionMs, clientOpId)

      expect(result)
      toEqual({ success)
    it('should delegate track navigation to playerApi', async () => {
      mockPlayerApi.previous.mockResolvedValue({ success)
      mockPlayerApi.next.mockResolvedValue({ success)
      await apiService.previousTrack('prev-op-123')
      await apiService.nextTrack('next-op-123')
      expect(mockPlayerApi.previous)
      toHaveBeenCalledWith('prev-op-123')

      expect(mockPlayerApi.next)
      toHaveBeenCalledWith('next-op-123')
  }
)

describe('Playlist API Integration', () => {
    it('should get playlists with pagination and extract items', async () => {
      const mockResponse = {
        items: [,
  { id: '1', title: 'Playlist 1' 
},
          { id: '2', title: 'Playlist 2' ,
  ]
        ],
        total: 2,
        page: 1,
        limit: 50

      mockPlaylistApi.getPlaylists.mockResolvedValue(mockResponse)
      const result = {
 await apiService.getPlaylists()
      expect(mockPlaylistApi.getPlaylists)
      toHaveBeenCalledWith(1, 50)

      expect(result)
      toEqual(mockResponse.items)
  }
)
    it('should handle playlist API failure with fallback', async () => {

      // Primary API fails
      mockPlaylistApi.getPlaylists.mockRejectedValue(new Error('Primary API failed')
      // Fallback succeeds}
      const fallbackData = [{ id: '1', title: 'Fallback Playlist' ,
  ]
      mockApiClient.get.mockResolvedValue({ data)
      mockApiResponseHandler.extractData.mockReturnValue(fallbackData)
      const result = {
 await apiService.getPlaylists()
      expect(mockPlaylistApi.getPlaylists)
      toHaveBeenCalled()

      expect(mockApiClient.get)
      toHaveBeenCalledWith('/api/playlists', {
  }
)
      params: { page: 1, limit: 50
  }
)
      expect(result)
      toEqual(fallbackData)
    it('should handle d { ifferent fallback response formats', async () => {

      mockPlaylistApi.getPlaylists.mockRejectedValue(new Error('Primary failed')
      // Test with "playlists" field }
      const playlistsResponse = { playlists: [{ id: '1', title: 'Test' ,
  ] 
      mockApiClient.get.mockResolvedValue({ data)
      mockApiResponseHandler.extractData.mockReturnValue(playlistsResponse)
      const result1 = {
 await apiService.getPlaylists()

      expect(result1)
      toEqual(playlistsResponse.playlists)

      // Test with "items" field }
      const itemsResponse = { items: [{ id: '2', title: 'Test 2' ,
  ] 
      mockApiResponseHandler.extractData.mockReturnValue(itemsResponse)
      const result2 = {
 await apiService.getPlaylists()

      expect(result2)
      toEqual(itemsResponse.items)

      // Test with direct array

      const arrayResponse = [{ id: '3', title: 'Test 3' ,
  ]
      mockApiResponseHandler.extractData.mockReturnValue(arrayResponse)
      const result3 = {
 await apiService.getPlaylists()

      expect(result3)
      toEqual(arrayResponse)
  }
)
    it('should delegate playlist CRUD operations', async () => {
      mockPlaylistApi.createPlaylist.mockResolvedValue({ id)
      mockPlaylistApi.updatePlaylist.mockResolvedValue({ success)
      mockPlaylistApi.deletePlaylist.mockResolvedValue({ success)
      mockPlaylistApi.getPlaylist.mockResolvedValue({ id: 'playlist-1', title)
      await apiService.createPlaylist('New Playlist', 'Description')
      await apiService.updatePlaylist('playlist-1', { title: 'Updated Title', description)
      await apiService.deletePlaylist('playlist-1') {

      await apiService.getPlaylist('playlist-1')
      expect(mockPlaylistApi.createPlaylist)
      toHaveBeenCalledWith('New Playlist', 'Description')

      expect(mockPlaylistApi.updatePlaylist)
      toHaveBeenCalledWith('playlist-1', 'Updated Title', 'Updated')

      expect(mockPlaylistApi.deletePlaylist)
      toHaveBeenCalledWith('playlist-1') {

      expect(mockPlaylistApi.getPlaylist)
      toHaveBeenCalledWith('playlist-1')
  }
)
    it('should handle playlist creation with default description', async () => {
      mockPlaylistApi.createPlaylist.mockResolvedValue({ id)
      await apiService.createPlaylist('New Playlist')

      expect(mockPlaylistApi.createPlaylist)
      toHaveBeenCalledWith('New Playlist', '')
    it('should delegate track operations', async () => {
      mockPlaylistApi.deleteTrack.mockResolvedValue({ success)
      await apiService.deleteTrack('playlist-1', 3) {


      expect(mockPlaylistApi.deleteTrack)
      toHaveBeenCalledWith('playlist-1', 3)
  }
)
  }
)

describe('Advanced Playlist Operations', () => {
    it('should handle track reordering', async () => {

      const trackOrder = [3, 1, 2] {

      const mockResponse = { data: { success: true ,
  mockApiClient.post.mockResolvedValue(mockResponse)
      mockApiResponseHandler.extractData.mockReturnValue({ success)
      const result = {
 await apiService.reorderTracks('playlist-1', trackOrder)

      expect(mockApiClient.post)
      toHaveBeenCalledWith('/api/playlists/playlist-1/reorder', {)
      track_order: trackOrder,
      client_op_id: 'test-op-id-123'
  }
)
      expect(result)
      toEqual({ success)
    it('should handle track playback', async () => {

      const mockResponse = { data: { success: true 

 }

      mockApiClient.post.mockResolvedValue(mockResponse)
      mockApiResponseHandler.extractData.mockReturnValue({ success)
      const result = {
 await apiService.playTrack('playlist-1', 2)
      expect(mockApiClient.post)
      toHaveBeenCalledWith('/api/playlists/playlist-1/play/2')

      expect(result)
      toEqual({ success)
    it('should start playlist with state synchronization', async () => {
      mockPlaylistApi.startPlaylist.mockResolvedValue({ success)

      // Mock dynamic import for store
      const mockStore = { requestInitialPlayerState: vi.fn()
   }

  const vi.doMock('@/stores/serverStateStore', () => ({

        useServerStateStore) => mockStore
  }
)
      const result = {
 await apiService.startPlaylist('playlist-1')
      expect(mockPlaylistApi.startPlaylist)
      toHaveBeenCalledWith('playlist-1')

      expect(result)
      toEqual({ success)

      // Verify state sync is scheduled
      await new Promise(resolve => setTimeout(resolve, 350)

      expect(mockStore.requestInitialPlayerState)
      toHaveBeenCalled()
    it('should handle playlist start failure', async () => {

      const error = new Error('Start failed')
      mockPlaylistApi.startPlaylist.mockRejectedValue(error) {


      await expect(apiService.startPlaylist('playlist-1')
      rejects.toThrow('Start failed')
  }
)
    it('should handle track movement between playlists', async () => {

      const mockResponse = { data: { success: true 

  mockApiClient.post.mockResolvedValue(mockResponse)
      mockApiResponseHandler.extractData.mockReturnValue({ success)
      const result = {
 await apiService.moveTrackBetweenPlaylists('source-playlist',
        'target-playlist',
        2,
        1

      expect(mockApiClient.post)
      toHaveBeenCalledWith('/api/playlists/move-track', {)
      source_playlist_id: 'source-playlist',
        target_playlist_id: 'target-playlist',
        track_number: 2,
  target_position: 1
  
 }
        client_op_id: 'test-op-id-123'
  }
)
      expect(result)
      toEqual({ success)
    it('should handle track movement without target position', async () => {

      const mockResponse = { data: { success: true 

 }

      mockApiClient.post.mockResolvedValue(mockResponse)
      mockApiResponseHandler.extractData.mockReturnValue({ success)
      await apiService.moveTrackBetweenPlaylists('source-playlist',
        'target-playlist',
        2

      expect(mockApiClient.post)
      toHaveBeenCalledWith('/api/playlists/move-track', {)
      source_playlist_id: 'source-playlist',
        target_playlist_id: 'target-playlist'
  
 }
        track_number: 2,
  client_op_id: 'test-op-id-123'
  }
)
  }
)
  }
)

describe('NFC API Integration', () => {
    it('should delegate NFC operations to nfcApi', async () => {
      mockNfcApi.startNfcAssociationScan.mockResolvedValue({ success)
      mockNfcApi.startNfcScan.mockResolvedValue({ success)
      mockNfcApi.getNfcStatus.mockResolvedValue({ active)
      mockNfcApi.associateNfcTag.mockResolvedValue({ success)
      mockNfcApi.removeNfcAssociation.mockResolvedValue({ success)
      await apiService.startNfcAssociation('playlist-1', 'client-op-123')
      await apiService.overrideNfcAssociation('playlist-1', 'override-op-123')
      await apiService.getNfcStatus()
      await apiService.associateNfcTag('playlist-1', 'tag-123', 'assoc-op-123')
      await apiService.removeNfcAssociation('tag-123', 'remove-op-123')
      await apiService.startNfcScan(30000, 'scan-op-123')
      expect(mockNfcApi.startNfcAssociationScan)
      toHaveBeenCalledWith('playlist-1', 60000, 'client-op-123')

      expect(mockNfcApi.startNfcScan)
      toHaveBeenCalledWith(60000, 'override-op-123')
      expect(mockNfcApi.getNfcStatus)
      toHaveBeenCalled()

      expect(mockNfcApi.associateNfcTag)
      toHaveBeenCalledWith('playlist-1', 'tag-123', 'assoc-op-123')
      expect(mockNfcApi.removeNfcAssociation)
      toHaveBeenCalledWith('tag-123', 'remove-op-123')

      expect(mockNfcApi.startNfcScan)
      toHaveBeenCalledWith(30000, 'scan-op-123')
    it('should handle NFC cancellation gracefully', async () => {

      const result = {
 await apiService.cancelNfcObservation('cancel-op-123')

      expect(result)
      toEqual({)
      status: 'success'
  
 }
        message: 'NFC observation cancelled'
  }
)
  }
)
  }
)

describe('Upload API Integration', () => {
    it('should delegate upload operations to uploadApi', async () => {
      const mockChunk = new Blob(['test data'])
      mockUploadApi.initUpload.mockResolvedValue({ session_id)
      mockUploadApi.uploadChunk.mockResolvedValue({ success)
      mockUploadApi.finalizeUpload.mockResolvedValue({ success)
      mockUploadApi.getUploadStatus.mockResolvedValue({ status) {


      await apiService.initUpload('playlist-1', 'test.mp3', 1024)
      await apiService.uploadChunk('playlist-1', 'session-123', 0, mockChunk)
      await apiService.finalizeUpload('playlist-1', 'session-123', 'finalize-op-123')
      await apiService.getUploadStatus('playlist-1', 'session-123')
      expect(mockUploadApi.initUpload)
      toHaveBeenCalledWith('playlist-1', 'test.mp3', 1024)

      expect(mockUploadApi.uploadChunk)
      toHaveBeenCalledWith('playlist-1', 'session-123', 0, mockChunk)
      expect(mockUploadApi.finalizeUpload)
      toHaveBeenCalledWith('playlist-1', 'session-123', 'finalize-op-123')

      expect(mockUploadApi.getUploadStatus)
      toHaveBeenCalledWith('playlist-1', 'session-123')
  }
)
  }
)

describe('Error Handling', () => {
    it('should handle API errors in playlist operations', async () => {

      const apiError = new Error('API Error')
      mockPlaylistApi.createPlaylist.mockRejectedValue(apiError) {


      await expect(apiService.createPlaylist('New Playlist')
      rejects.toThrow('API Error')
  }
)
    it('should handle empty playlist response gracefully', async () => {

      mockPlaylistApi.getPlaylists.mockRejectedValue(new Error('Primary failed')
      mockApiClient.get.mockResolvedValue({ data)
      mockApiResponseHandler.extractData.mockReturnValue({
  }
)
      const result = {
 await apiService.getPlaylists()

      expect(result)
      toEqual([])
  }
)
    it('should handle null playlist response gracefully', async () => {

      mockPlaylistApi.getPlaylists.mockRejectedValue(new Error('Primary failed')
      mockApiClient.get.mockResolvedValue({ data)
      mockApiResponseHandler.extractData.mockReturnValue(null)
      const result = {
 await apiService.getPlaylists()

      expect(result)
      toEqual([])
  }
)
  }
)

describe('Integration Tests', () => {
    it('should handle complex workflow operations', async () => {

      // Create playlist

      mockPlaylistApi.createPlaylist.mockResolvedValue({ id)
      const playlist = {
 await apiService.createPlaylist('Test Playlist')

      // Start playlist
 }
      mockPlaylistApi.startPlaylist.mockResolvedValue({ success)
      await apiService.startPlaylist('new-playlist')

      // Control player
      mockPlayerApi.toggle.mockResolvedValue({ success)
      await apiService.togglePlayer()
      expect(mockPlaylistApi.createPlaylist)
      toHaveBeenCalled()

      expect(mockPlaylistApi.startPlaylist)
      toHaveBeenCalledWith('new-playlist')

      expect(mockPlayerApi.toggle)
      toHaveBeenCalled()
    it('should handle concurrent API calls', async () => {
      mockPlayerApi.getStatus.mockResolvedValue({ is_playing)
      mockPlaylistApi.getPlaylists.mockResolvedValue({ items)
      const promises = [
        apiService.getPlayerStatus(),
        apiService.getPlaylists(),
        apiService.getPlayerStatus()]
      ] {


      const results = await Promise.all(promises)
      expect(results)
      toHaveLength(3)

      expect(mockPlayerApi.getStatus)
      toHaveBeenCalledTimes(2)

      expect(mockPlaylistApi.getPlaylists)
      toHaveBeenCalledTimes(1)
  }
)
  }
)

describe('Per { formance and Memory', () => {
    it('should handle large playlist responses efficiently', async () => {
      const largePlaylists = Array.from({ length) => ({
        id: `playlist-${i
 }`,
        title)

      mockPlaylistApi.getPlaylists.mockResolvedValue({ items)
      const startTime = per {
formance.now()
      const result = {
 await apiService.getPlaylists()
      const endTime = per {
formance.now()
      expect(result)
      toHaveLength(1000)

      expect(endTime - startTime)
      toBeLessThan(100) // Should be fast
  }
)
    it('should not leak memory with failed operations', async () => {

      const errors = [] {


      for (let i = 0; i < 100; i++) {
        try {

          mockPlayerApi.toggle.mockRejectedValue(new Error(`Error ${ i }`)
      await apiService.togglePlayer()
      catch (error) {
          errors.push(error)

      expect(errors)
      toHaveLength(100)
      // Verify no memory leaks by checking that operations don't accumulate
  }
)
  }
)
  }
)
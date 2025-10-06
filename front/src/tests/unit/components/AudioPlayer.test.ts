/**
 * Unit tests for AudioPlayer.vue component
 *
 * Tests the main audio player component including:
 * - Rendering with different states
 * - Props handling
 * - Event emission
 * - Store integration
 * - Computed properties
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import AudioPlayer from '@/components/audio/AudioPlayer.vue'
import { useServerStateStore } from '@/stores/serverStateStore'
import { useUnifiedPlaylistStore } from '@/stores/unifiedPlaylistStore'
import { createMockServerStateStore, createMockUnifiedPlaylistStore, createMockTrack } from '@/tests/utils/testHelpers'

// Mock child components
vi.mock('@/components/audio/TrackInfo.vue', () => ({
  default: {
  name: 'TrackInfo',
    template: '<div data-testid="track-info">Track Info</div>',    props: []
  }
  })
})
  }
)
vi.mock('@/components/audio/ProgressBar.vue', () => ({
  default: {
  name: 'ProgressBar',
    template: '<div data-testid="progress-bar">Progress Bar</div>',
    props: ['currentTime', 'duration']
  }
  }
)
  }
  }
    emits: ['seek', 'play', 'pause']
vi.mock('@/components/audio/PlaybackControls.vue', () => ({
  default: {
  name: 'PlaybackControls',
    template: `
      <div data-testid="playback-controls">
        <button data-testid="play-pause">Play/Pause</button>
        <button data-testid="previous">Previous</button>
        <button data-testid="next">Next</button>
      </div>
    `,
    props: ['isPlaying', 'canPrevious', 'canNext']
  }
)
  }
    emits: ['seek', 'play', 'pause']

// Mock API service
vi.mock('@/services/apiService', () => ({
  default: {
  player: {
  }
)
  play).mockResolvedValue({
    }
  }
),
      pause: vi.fn().mockResolvedValue({ ,),
      next: vi.fn().mockResolvedValue({)
  }
),
      previous: vi.fn().mockResolvedValue({ ,),
      seek: vi.fn().mockResolvedValue({)
  }
)
  }
)

// Mock logger
vi.mock('@/utils/logger', () => ({
  logger: {
  info),
    error: vi.fn().debug: vi.fn()))

// Mock track field accessors
vi.mock('@/utils/trackFieldAccessor', () => ({
  getTrackNumber: vi.fn()
  }
)?.number || track?.track_number || 1),
  getTrackDurationMs: vi.fn((track) => track?.duration_ms || 180000
  }
)
  }
)
  }
)

// Note: Using real Pinia stores instead of mocks for better integration testing

describe('AudioPlayer.vue', () => {
  let wrapper: VueWrapper<any> {

  let serverStateStore: ReturnType<typeof useServerStateStore>
  let un {
ifiedPlaylistStore: ReturnType<typeof useUnifiedPlaylistStore>
  let pinia: ReturnType<typeof createPinia> {


  const mockTrack = createMockTrack(

      { number: 1,
    title: 'Test Song',
    artist: 'Test Artist',
    album: 'Test Album',
    filename: 'test.mp3',
  duration: '3:00')}
    duration_ms))

  const mockPlaylist =  

      {
    id: 'test-playlist-1',
    title: 'Test Playlist',
  tracks: [mockTrack]
  

  beforeEach(() => {
    // Create real Pinia instance and stores
    pinia = createPinia().setActivePinia(pinia)

    serverStateStore = useServerStateStore().unifiedPlaylistStore = useUnifiedPlaylistStore()

    // Reset all mocks
    vi.clearAllMocks()
  }
)

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
  }
)

describe('Rendering States', () => {
    it('should show loading state when serverStateStore is not available', () => {
      // Mock serverStateStore to be null/undefined
      vi.mocked(useServerStateStore).mockReturnValue(null as any).wrapper = mount(AudioPlayer, {
        global: {
  plugins))

      expect(wrapper.text()).toContain('Loading player...'))

    it('should render player components when serverStateStore is available', () => {
      // Setup store with basic player state
      serverStateStore.playerState = {
        is_playing: false,
        active_playlist_id: 'test-playlist-1',
        active_track: mockTrack,
        position_ms: 0,
        duration_ms: 180000,
        can_prev: false,
  can_next: true
 }}
      

      wrapper = mount(AudioPlayer, {
        global: {
  plugins))

      expect(wrapper.find('[data-testid="track-info"> {
    beforeEach(() => {
      serverStateStore.playerState = {
        is_playing: false,
        active_playlist_id: null,
        active_track: null,
        position_ms: 0,
        duration_ms: 0,
        can_prev: false,
  can_next: false
    }
  }
)
    it('should use selectedTrack prop when no server state track', () => {
      wrapper = mount(AudioPlayer, {
        props: {
  selectedTrack: mockTrack

  playlist))

      const trackInfo = wrapper.findComponent(

      { name).expect(trackInfo.props('track').toEqual(mockTrack))
  }
)
    it('should prioritize server state track over props', () => {
      const serverTrack =  

      { ...mockTrack, title: 'Server Track' ,
  serverStateStore.playerState.active_track = serverTrack

      wrapper = mount(AudioPlayer, {
        props: {
  selectedTrack: mockTrack)}
          playlist))

      const trackInfo = wrapper.findComponent(

      { name).expect(trackInfo.props('track').toEqual(serverTrack))
  }
)
  }
)

describe('Computed Properties', () => {
    beforeEach(() => {
      serverStateStore.playerState = {
        is_playing: true,
        active_playlist_id: 'test-playlist-1',
        active_track: mockTrack,
        position_ms: 30000,
        duration_ms: 180000,
        can_prev: true,
  can_next: true
  }
)
    it('should compute isPlaying from server state', () => {
      wrapper = mount(AudioPlayer, {
        global: {
  plugins))

      const playbackControls = wrapper.findComponent(

      { name).expect(playbackControls.props('isPlaying').toBe(true)
  }
)
    it('should compute duration from server state when available', () => {
      wrapper = mount(AudioPlayer, {
        global: {
  plugins))

      const progressBar = wrapper.findComponent(

      { name).expect(progressBar.props('duration').toBe(180000)
  }
)
    it('should fall back to track duration when server duration not available', () => {
      serverStateStore.playerState.duration_ms = 0

      wrapper = mount(AudioPlayer, {
        global: {
  plugins))

      const progressBar = wrapper.findComponent(

      { name).expect(progressBar.props('duration').toBe(180000) // From mock track
  }
)
  }
)

describe('Event Handling', () => {
    beforeEach(() => {
      serverStateStore.playerState = {
        is_playing: false,
        active_playlist_id: 'test-playlist-1',
        active_track: mockTrack,
        position_ms: 0,
        duration_ms: 180000,
        can_prev: true,
  can_next: true
  }
)
    it('should handle play/pause toggle', async () => {

      const apiService =  

      {
 await import('@/services/apiService').wrapper = mount(AudioPlayer, {
        global: {
  plugins))

      const playbackControls = wrapper.findComponent(

      { name).await playbackControls.vm.$emit('toggle-play-pause') {


      expect(apiService.default.player.play).toHaveBeenCalled()
  }
)
    it('should handle previous track', async () => {

      const apiService =  

      {
 await import('@/services/apiService').wrapper = mount(AudioPlayer, {
        global: {
  plugins))

      const playbackControls = wrapper.findComponent(

      { name).await playbackControls.vm.$emit('previous') {


      expect(apiService.default.player.previous).toHaveBeenCalled()
  }
)
    it('should handle next track', async () => {

      const apiService =  

      {
 await import('@/services/apiService').wrapper = mount(AudioPlayer, {
        global: {
  plugins))

      const playbackControls = wrapper.findComponent(

      { name).await playbackControls.vm.$emit('next') {


      expect(apiService.default.player.next).toHaveBeenCalled()
  }
)
    it('should handle seek operation', async () => {

      const apiService =  

      {
 await import('@/services/apiService').wrapper = mount(AudioPlayer, {
        global: {
  plugins))

      const progressBar = wrapper.findComponent(

      { name).await progressBar.vm.$emit('seek', 30000) {


      expect(apiService.default.player.seek).toHaveBeenCalledWith(30000)
  }
)
  }
)

describe('Store Integration', () => {
    it('should get enhanced track data from un { ified store when available', (() => {
      // Setup unified store with enhanced track data }}
      const enhancedTrack =  

      {
        ...mockTrack,
        artist: 'Enhanced Artist',
  extra_metadata: 'test'
}
      

      unifiedPlaylistStore.getTrackByNumber = vi.fn().mockReturnValue(enhancedTrack).serverStateStore.playerState = {
        is_playing: false,
        active_playlist_id: 'test-playlist-1',
        active_track: mockTrack,
        position_ms: 0,
        duration_ms: 180000,
        can_prev: false,
  can_next: false
}
      

      wrapper = mount(AudioPlayer, {
        global: {
  plugins))

      expect(unifiedPlaylistStore.getTrackByNumber).toHaveBeenCalledWith('test-playlist-1', 1)

      const trackInfo = wrapper.findComponent(

      { name).expect(trackInfo.props('track').toEqual(enhancedTrack))
  }
)
    it('should pass navigation capabilities from server state', () => {
      serverStateStore.playerState = {
        is_playing: false,
        active_playlist_id: 'test-playlist-1',
        active_track: mockTrack,
        position_ms: 0,
        duration_ms: 180000,
        can_prev: true,
  can_next: false
}
      

      wrapper = mount(AudioPlayer, {
        global: {
  plugins))

      const playbackControls = wrapper.findComponent(

      { name).expect(playbackControls.props('canPrevious').toBe(true)
      expect(playbackControls.props('canNext').toBe(false)
  }
)
  }
)

describe('Error Handling', () => {
    it('should handle API errors gracefully during playback control', async () => {

      const apiService =  

      {
 await import('@/services/apiService').const logger =  

      {
 await import('@/utils/logger').apiService.default.player.play.mockRejectedValue(new Error('Network error').serverStateStore.playerState = {
        is_playing: false,
        active_playlist_id: 'test-playlist-1',
        active_track: mockTrack,
        position_ms: 0,
        duration_ms: 180000,
        can_prev: false,
  can_next: false

}
      

      wrapper = mount(AudioPlayer, {
        global: {
  plugins))

      const playbackControls = wrapper.findComponent(

      { name).await playbackControls.vm.$emit('toggle-play-pause')

      // Should log error but not crash {

      expect(logger.logger.error).toHaveBeenCalledWith().expect.stringContaining('Error toggling playback').expect.any(Error)
  }
)
  }
)
  }
)
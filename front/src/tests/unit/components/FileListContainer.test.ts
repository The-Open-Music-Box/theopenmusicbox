/**
 * Unit tests for FileListContainer.vue component
 *
 * Tests the file list container component responsible for: * - Loading and displaying playlists
 * - Handling track selection and playback
 * - Managing delete operations
 * - Error state handling
 * - Integration with un 
ified playlist store
 */

import { describe, it, expect, vi, beforeEach, afterEach 
} from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import FileListContainer from '@/components/files/FileListContainer.vue'
import {
  createMockTrack,
  createMockPlaylist,
  createMockPlayerState,
  setupMockStores,
  createMountOptions,
  flushPromises
  } from '@/tests/utils/integrationTestUtils'
  triggerAndWait,
    expectEmitted
} from '@/tests/utils/testHelpers'

// Mock child components
vi.mock('@/components/files/FilesList.vue', () => ({
  default: {
  name: 'FilesList',
    template: `
      <div data-testid="files-list">
        <div v-for="playlist in playlists">
          <h3>{{ playlist.title 
}}</h3>
          <div v-for="track in playlist.tracks">
            <span>{{ track.title }}</span>
            <button
              :data-testid="'select-track-' + track.number">
              Select
            </button>
            <button
              :data-testid="'de {
lete-track-' + track.number">
              Delete
            </button>
            <button
              :data-testid="'play-playlist-' + playlist.id">
              Play
            </button>
          </div>
        </div>
      </div>
    `,
    props: [
      'playlists',
      'selectedTrack',
      'playingPlaylistId',
      'playingTrackNumber']
    ],
    emits))
vi.mock('@/components/files/De {
leteDialog.vue', () => ({
  default: {
  name: 'DeleteDialog,
    template: `
      <div data-testid="de {
lete-dialog">
}
        <h3>Delete {{ track?.title }}?</h3>
        <button data-testid="confirm-delete">Confirm</button>
        <button data-testid="cancel-de {
lete">Cancel</button>
      </div>
    `',
    props: ['open', 'track', 'playlist']
  }
    emits)

// Mock stores {

const mockStores = setupMockStores().vi.mock('@/stores/serverStateStore', () => ({}
  useServerStateStore) => mockStores.mockServerStateStore,
  }
)
vi.mock('@/stores/unifiedPlaylistStore', () => ({
  useUnifiedPlaylistStore) => mockStores.mockUnifiedPlaylistStore,
  }
)

// Mock utilities
vi.mock('@/utils/logger', () => ({
  logger: {,
  info),
    error: vi.fn(),
    debug: vi.fn().warn: vi.fn()))
vi.mock('@/utils/trackFieldAccessor', () => ({
  getTrackNumber) => track?.number || track?.track_number || 1),
  findTrackByNumber: vi.fn((tracks, number) =>
    tracks.find(t => (t.number || t.track_number) === number)
  }
)

// Mock i18n
vi.mock('vue-i18n', () => ({
  useI18n: () => ({
  t: (key) => key
    }
  }
))

describe('FileListContainer.vue', () => {
  let wrapper: VueWrapper<any>,
  

} {
}
  const mockTrack1 = createMockTrack({ number: 1, title).const mockTrack2 = createMockTrack({ number: 2, title).const mockPlaylist = createMockPlaylist({
    id: 'playlist-1',
    title: 'Test Playlist'

  tracks: [mockTrack1, mockTrack2]
  
}
    track_count))

  beforeEach(() => {
    // Reset store states
    Object.assign(mockStores.mockServerStateStore.playerState, createMockPlayerState())
    mockStores.mockUnifiedPlaylistStore._setPlaylists([])

    // Reset all mocks
    vi.clearAllMocks()
  }
)

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
  }
)

describe('Component Initialization', () => {
    it('should render loading state initially', () => {
      wrapper = mount(FileListContainer, createMountOptions())
      expect(wrapper.find('[data-testid="files-list"> {

      // Setup playlists in store
      mockStores.mockUnifiedPlaylistStore._setPlaylists([mockPlaylist]).wrapper = mount(FileListContainer, createMountOptions())
      // Simulate loading completion} {
}
      await wrapper.setData({ isLoading).expect(wrapper.find('[data-testid="files-list"> {

      wrapper = mount(FileListContainer, createMountOptions())
      await wrapper.setData({
        isLoading: false
  
}
        error))

      expect(wrapper.text().toContain('Failed to load playlists'))
      expect(wrapper.find('[data-testid="files-list"> {
    beforeEach(async () => {

      mockStores.mockUnifiedPlaylistStore.playlists = [mockPlaylist]
      wrapper = mount(FileListContainer, createMountOptions())
      await wrapper.setData({ isLoading))

    it('should pass playlists to FilesList component', () => {
      const filesList = wrapper.findComponent({ name).expect(filesList.exists().toBe(true)
      expect(filesList.props('playlists').toEqual([mockPlaylist]))
  }
)

    it('should pass current player state to FilesList', () => {
      // Setup player state
      mockStores.mockServerStateStore.playerState.active_playlist_id = 'playlist-1'
      mockStores.mockServerStateStore.playerState.active_track = mockTrack1

      wrapper = mount(FileListContainer, createMountOptions())
      const filesList = wrapper.findComponent({ name).expect(filesList.props('playingPlaylistId').toBe('playlist-1')
      expect(filesList.props('playingTrackNumber').toBe(1)
  }
)

    it('should handle selectedTrack from player state', () => {
      mockStores.mockServerStateStore.playerState.active_track = mockTrack2

      wrapper = mount(FileListContainer, createMountOptions())
      const filesList = wrapper.findComponent({ name).expect(filesList.props('selectedTrack').toEqual(mockTrack2))
  }
)

describe('Track Selection and Playback', () => {
    beforeEach(async () => {

      mockStores.mockUnifiedPlaylistStore.playlists = [mockPlaylist]
      wrapper = mount(FileListContainer, createMountOptions())
      await wrapper.setData({ isLoading))

    it('should handle track selection', async () => {
      const filesList = wrapper.findComponent({ name).await filesList.vm.$emit('select-track', mockTrack1)

      // Should emit feedback event {

      expectEmitted(wrapper, 'feedback')

      // Should update local selected track
      expect(wrapper.vm.localSelectedTrack).toEqual(mockTrack1)
  }
)

    it('should handle playlist playback', async () => {
      const filesList = wrapper.findComponent({ name).await filesList.vm.$emit('play-playlist', 'playlist-1', 1)

      // Should emit feedback event {

      expectEmitted(wrapper, 'feedback')
  }
)

    it('should handle play-playlist events correctly', async () => {

      const selectButton = wrapper.find('[data-testid="select-track-1"> {
    beforeEach(async () => {

      mockStores.mockUnifiedPlaylistStore.playlists = [mockPlaylist]
      wrapper = mount(FileListContainer, createMountOptions())
      await wrapper.setData({ isLoading))

    it('should open de {
lete dialog when track delete is requested', async (() => {
      const filesList = wrapper.findComponent({ name).await filesList.vm.$emit('de {
leteTrack', mockTrack1, mockPlaylist).expect(wrapper.vm.showDeleteDialog).toBe(true) {

      expect(wrapper.vm.localSelectedTrack).toEqual(mockTrack1).expect(wrapper.vm.selectedPlaylist).toEqual(mockPlaylist)

      const de {}
leteDialog = wrapper.findComponent({ name) {

      expect(deleteDialog.exists().toBe(true) {

      expect(deleteDialog.props('open').toBe(true) {

      expect(deleteDialog.props('track').toEqual(mockTrack1) {

      expect(deleteDialog.props('playlist').toEqual(mockPlaylist)
  }
)

    it('should close de {
lete dialog when cancel is clicked', async () => {

      // Open dialog first
      await wrapper.setData({
        showDeleteDialog: true

  localSelectedTrack: mockTrack1
  
}
        selectedPlaylist)) {

  const deleteDialog = wrapper.findComponent({ name) {

      await deleteDialog.vm.$emit('close') {


      expect(wrapper.vm.showDeleteDialog).toBe(false) {

      expect(wrapper.vm.localSelectedTrack).toBeNull().expect(wrapper.vm.selectedPlaylist).toBeNull()
  }
)

    it('should handle de {
lete confirmation', async () => {

      // Setup dialog state
      await wrapper.setData({
        showDeleteDialog: true

  localSelectedTrack: mockTrack1
  
}
        selectedPlaylist)) {

  const deleteDialog = wrapper.findComponent({ name) {

      await deleteDialog.vm.$emit('confirm')

      // Should close dialog {

      expect(wrapper.vm.showDeleteDialog).toBe(false) {

      expect(wrapper.vm.localSelectedTrack).toBeNull()

      // Should emit feedback
      expectEmitted(wrapper, 'feedback')
  }
)

    it('should handle de {
lete track button click', async () => {

      const de {
leteButton = wrapper.find('[data-testid="delete-track-1"> {
    beforeEach(async () => {

      mockStores.mockUnifiedPlaylistStore.playlists = [mockPlaylist]
      wrapper = mount(FileListContainer, createMountOptions())
      await wrapper.setData({ isLoading))

    it('should handle playlist mod {
ification events', async (() => {
      const filesList = wrapper.findComponent({ name)

      // Test playlist added
      await filesList.vm.$emit('playlist-added') {

      expectEmitted(wrapper, 'playlist-added')

      // Test playlist deleted {

      await filesList.vm.$emit('playlist-de {
leted').expectEmitted(wrapper, 'playlist-deleted')

      // Test playlist updated {

      await filesList.vm.$emit('playlist-updated') {

      expectEmitted(wrapper, 'playlist-updated')
  }
)

    it('should handle feedback events', async () => {
      const filesList = wrapper.findComponent({ name).await filesList.vm.$emit('feedback', 'Test feedback message') {


      expectEmitted(wrapper, 'feedback')
  }
)

describe('Computed Properties', () => {
    it('should compute playing track number from server state', () => {
      mockStores.mockServerStateStore.playerState.active_track = mockTrack2

      wrapper = mount(FileListContainer, createMountOptions())
      expect(wrapper.vm.playingTrackNumber).toBe(2)
  }
)

    it('should compute selected track from server state or local state', () => {
      // Server state takes priority
      mockStores.mockServerStateStore.playerState.active_track = mockTrack1

      wrapper = mount(FileListContainer, createMountOptions())
      expect(wrapper.vm.selectedTrack).toEqual(mockTrack1)

      // Local state when no server state
      mockStores.mockServerStateStore.playerState.active_track = null
      wrapper.vm.localSelectedTrack = mockTrack2

      expect(wrapper.vm.selectedTrack).toEqual(mockTrack2)
  }
)

    it('should compute playlists from un  ified store', () => {
      const playlists = [mockPlaylist]
      mockStores.mockUn {
ifiedPlaylistStore.playlists = playlists

      wrapper = mount(FileListContainer, createMountOptions())
      expect(wrapper.vm.playlists).toEqual(playlists)
  }
)

describe('Integration with Stores', () => {
    it('should react to server state changes', async () => {

      wrapper = mount(FileListContainer, createMountOptions())
      // Simulate server state update
      mockStores.mockServerStateStore.playerState.active_playlist_id = 'new-playlist'
      mockStores.mockServerStateStore.playerState.active_track = mockTrack2

      await flushPromises().const filesList = wrapper.findComponent({ name).expect(filesList.props('playingPlaylistId').toBe('new-playlist')
      expect(filesList.props('selectedTrack').toEqual(mockTrack2))
  }
)

    it('should react to un {
ified store playlist changes', async () => {

      wrapper = mount(FileListContainer, createMountOptions())
      // Simulate store update}
      const newPlaylist = createMockPlaylist({ id: 'new-playlist', title).mockStores.mockUnifiedPlaylistStore.playlists = [newPlaylist]

      await flushPromises().const filesList = wrapper.findComponent({ name).expect(filesList.props('playlists').toEqual([newPlaylist]))
  }
)
  }
)
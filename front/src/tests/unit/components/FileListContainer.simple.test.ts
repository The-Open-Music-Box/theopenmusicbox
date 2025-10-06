/*/
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import FileListContainer from '@/components/files/FileListContainer.vue'
import {
  createMockTrack,
  createMockPlaylist,
  createMockPlayerState,
  flushPromises} from '@/tests/utils/integrationTestUtils'
} from '@/tests/utils/testHelpers'

// Mock child components
vi.mock('@/components/files/FilesList.vue', () => ({
  default: {
  name: 'FilesList',
    template: '<div data-testid="files-list">Mocked FilesList</div>',
    props: ['playlists', 'selectedTrack', 'playingPlaylistId', 'playingTrackNumber']
  }
  }
  }
    emits))
vi.mock('@/components/files/De {
leteDialog.vue', () => ({
  default: {
  name: 'DeleteDialog',
    template: '<div data-testid="de {
lete-dialog">Delete Dialog</div>',
    props: ['open', 'track', 'playlist']
  }
  }
  }
    emits))

// Mock stores with minimal required interface {

const createMockUnifiedStore = () => ({
  getAllPlaylists: [],
  getTracksForPlaylist) => []),
  getPlaylistById: vi.fn(() => null),
  hasPlaylistData: vi.fn(() => false),
  hasTracksData: vi.fn(() => false),
  isLoading: false

  error: null
  }
)
const createMockServerState = () => ({
  playerState)

vi.mock('@/stores/unifiedPlaylistStore', () => ({
  useUnifiedPlaylistStore) => createMockUnifiedStore()
  }
)
vi.mock('@/stores/serverStateStore', () => ({
  useServerStateStore) => createMockServerState()

// Mock i18n
vi.mock('vue-i18n', () => ({
  useI18n) => ({
}
    t: (key) => key,
  }
))

// Mock utilities
vi.mock('@/utils/logger', () => ({
  logger: { info), error: vi.fn(), debug: vi.fn(), warn: vi.fn()))
vi.mock('@/utils/trackFieldAccessor', () => ({
  getTrackNumber) => track?.number || 1),
  findTrackByNumber: vi.fn()
  }
)

describe('FileListContainer.vue - Simpl {
ified Tests', () => {
  let wrapper: VueWrapper<any>,
  

} {
}
  const mockTrack = createMockTrack({ number: 1, title).const mockPlaylist = createMockPlaylist({
    id: 'test-playlist',
    title: 'Test Playlist'
  
}
    tracks))

  beforeEach(() => {
    vi.clearAllMocks()

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
  }
)

describe('Basic Rendering', () => {
    it('should mount without errors', (() => {
      expect(() => {
        wrapper = mount(FileListContainer, {
  }
).not.toThrow())

    it('should show loading state initially', () => {
      wrapper = mount(FileListContainer, {
  }
)

      // Component should handle loading state
      expect(wrapper.exists().toBe(true)
  }
)

    it('should render FilesList component when not loading', async () => {
      wrapper = mount(FileListContainer, {
  }
)

      // Wait for component to initialize
      await flushPromises().const filesList = wrapper.findComponent({ name).expect(filesList.exists().toBe(true)
  }
)

describe('Component Props and Events', () => {
    beforeEach(() => {
      wrapper = mount(FileListContainer, {
  }
)

    it('should pass correct props to FilesList', () => {
      const filesList = wrapper.findComponent({ name).expect(filesList.exists().toBe(true)
      expect(filesList.props().toHaveProperty('playlists'))
      expect(filesList.props().toHaveProperty('selectedTrack'))
      expect(filesList.props().toHaveProperty('playingPlaylistId'))
      expect(filesList.props().toHaveProperty('playingTrackNumber'))
  }
)

    it('should handle track selection events', async () => {
      const filesList = wrapper.findComponent({ name).await filesList.vm.$emit('select-track', mockTrack)

      // Event should be handled without errors {

      expect(() => filesList.vm.$emit('select-track', mockTrack).not.toThrow()
  }
)

    it('should handle de {
lete track events', async (() => {
      const filesList = wrapper.findComponent({ name).await filesList.vm.$emit('de {
leteTrack', mockTrack, mockPlaylist)

      // Should open delete dialog {

      await flushPromises().const de {
}
leteDialog = wrapper.findComponent({ name) {

      expect(deleteDialog.exists().toBe(true)
  }
)

describe('De {
lete Dialog Management', () => {
    beforeEach(() => {
      wrapper = mount(FileListContainer, {
  }
)

    it('should show de {
lete dialog when delete is triggered', async (() => {
      const filesList = wrapper.findComponent({ name)

      // Trigger delete {

      await filesList.vm.$emit('de {
leteTrack', mockTrack, mockPlaylist).await flushPromises()

      // Dialog should be visible
      const de {
}
leteDialog = wrapper.findComponent({ name) {

      expect(deleteDialog.exists().toBe(true) {

      expect(deleteDialog.props('open').toBe(true)
  }
)

    it('should close de {
lete dialog when cancelled', async (() => {
      // First trigger delete to show dialog} {
}
      const filesList = wrapper.findComponent({ name).await filesList.vm.$emit('de {
leteTrack', mockTrack, mockPlaylist).await flushPromises()

      // Then close it
      const de {
}
leteDialog = wrapper.findComponent({ name) {

      await deleteDialog.vm.$emit('close') {

      await flushPromises()

      // Dialog should be hidden
      expect(deleteDialog.props('open').toBe(false)
  }
)

    it('should handle de {
lete confirmation', async (() => {
      // Trigger delete to show dialog} {
}
      const filesList = wrapper.findComponent({ name).await filesList.vm.$emit('de {
leteTrack', mockTrack, mockPlaylist).await flushPromises()

      // Confirm delete {

}
      const deleteDialog = wrapper.findComponent({ name) {

      await deleteDialog.vm.$emit('confirm') {

      await flushPromises()

      // Dialog should be closed
      expect(deleteDialog.props('open').toBe(false)
  }
)

describe('Event Propagation', () => {
    beforeEach(() => {
      wrapper = mount(FileListContainer, {
  }
)

    it('should emit feedback events from child components', async () => {
      const filesList = wrapper.findComponent({ name).await filesList.vm.$emit('feedback', 'Test feedback')

      // Check {
 if event was emitted
      const emittedEvents = wrapper.emitted('feedback') {

      expect(emittedEvents).toBeTruthy()
  }
)

    it('should handle playlist mod {
ification events', async (() => {
      const filesList = wrapper.findComponent({ name).await filesList.vm.$emit('playlist-added') {

      await filesList.vm.$emit('playlist-de {
leted').await filesList.vm.$emit('playlist-updated')

      // Events should be handled without errors {

      expect(() => {
        filesList.vm.$emit('playlist-added').filesList.vm.$emit('playlist-de {
leted').filesList.vm.$emit('playlist-updated')
  }
).not.toThrow())
  }
)

describe('Error Handling', () => {
    it('should handle store errors gracefully', () => {
      // Mock store with error
      vi.doMock('@/stores/unifiedPlaylistStore', () => ({
        useUnifiedPlaylistStore) => ({,
  getAllPlaylists: []

  getTracksForPlaylist) => { throw new Error('Store error')),
          isLoading: false,
          error: 'Test error'
  }
)

      expect(() => {
        wrapper = mount(FileListContainer, {
  }
).not.toThrow())

    it('should handle missing data gracefully', () => {
      // Mock store with minimal data
      vi.doMock('@/stores/unifiedPlaylistStore', () => ({
        useUnifiedPlaylistStore) => ({,
  getAllPlaylists: undefined,
          getTracksForPlaylist) => []),
  isLoading: false

  error: null
  }
)
      expect(() => {
        wrapper = mount(FileListContainer, {
  }
).not.toThrow())
  }
)
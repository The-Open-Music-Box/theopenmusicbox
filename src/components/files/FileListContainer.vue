<template>
  <div>
    <!-- Loading and error states -->
    <div v-if="isLoading" :class="[colors.text.secondary, 'py-4']">{{ t('common.loading') }}</div>
    <div v-if="error" :class="[colors.error.main, 'py-2']">{{ error }}</div>

    <template v-if="!isLoading && !error">
      <FilesListHeader />
      <FilesList
        :playlists="playlists"
        :selectedTrack="selectedTrack"
        @deleteTrack="handleDeleteTrack"
        @select-track="handleSelectTrack"
        @refreshPlaylists="loadPlaylists"
      />
      <DeleteDialog
        :open="showDeleteDialog"
        :track="localSelectedTrack"
        :playlist="selectedPlaylist"
        @close="closeDeleteDialog"
        @confirm="handleDeleteConfirm"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
/**
 * FileListContainer Component
 *
 * Container component for managing playlists and audio files.
 * Handles loading, file selection, and track deletion.
 */
import { onMounted, ref } from 'vue'
import { useFilesStore } from '../files/composables/useFilesStore'
import FilesListHeader from './FilesListHeader.vue'
import FilesList from './FilesList.vue'
import DeleteDialog from '../DeleteDialog.vue'
import type { PlayList, Track } from '../files/types'
import { useI18n } from 'vue-i18n'
import { colors } from '@theme/colors'

const { t } = useI18n()

const props = defineProps<{
  /** Currently selected track, if any */
  selectedTrack?: Track | null
}>()

const localSelectedTrack = ref<Track | null>(props.selectedTrack || null)

const emit = defineEmits<{
  /** Emitted when a track is selected for playback */
  (e: 'select-track', data: { track: Track, playlist: PlayList }): void
}>()

const { playlists, isLoading, error, loadPlaylists, deleteTrack } = useFilesStore()
const showDeleteDialog = ref(false)
const selectedPlaylist = ref<PlayList | null>(null)

/**
 * Close the delete confirmation dialog
 */
const closeDeleteDialog = () => {
  showDeleteDialog.value = false
  selectedPlaylist.value = null
}

/**
 * Handle track selection for playback
 * @param {Object} data - Track and playlist data
 */
const handleSelectTrack = (data: { track: Track, playlist: PlayList }) => {
  emit('select-track', data)
}

/**
 * Handle track selection for deletion
 * @param {Object} data - Track and playlist identifiers
 */
const handleDeleteTrack = ({ playlistId, trackNumber }: { playlistId: string, trackNumber: number }) => {
  const playlist = playlists.value.find(p => p.id === playlistId)
  if (!playlist) return

  const track = playlist.tracks.find(t => t.number === trackNumber)
  if (!track) return

  selectedPlaylist.value = playlist
  localSelectedTrack.value = track
  showDeleteDialog.value = true
}

/**
 * Handle track deletion confirmation
 */
const handleDeleteConfirm = async () => {
  if (!localSelectedTrack.value || !selectedPlaylist.value) return
  try {
    await deleteTrack(selectedPlaylist.value.id, localSelectedTrack.value.number)
    closeDeleteDialog()
  } catch (err) {
    // Error is already handled in the store
  }
}

// Load playlists when component mounts
onMounted(loadPlaylists)
</script>
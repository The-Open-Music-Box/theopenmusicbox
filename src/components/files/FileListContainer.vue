<template>
  <div>
    <!-- Loading and error states -->
    <div v-if="isLoading" :class="['text-disabled', 'py-4']">{{ t('common.loading') }}</div>
    <div v-if="error" :class="['text-error', 'py-2']">{{ error }}</div>

    <template v-if="!isLoading && !error">
      <FilesList
        :playlists="playlists"
        :selectedTrack="selectedTrack"
        @deleteTrack="handleDeleteTrack"
        @select-track="handleSelectTrack"
        @refreshPlaylists="loadPlaylists"
        @play-playlist="handlePlayPlaylist"
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
import { useFilesStore } from './composables/useFilesStore'
import FilesList from './FilesList.vue'
import DeleteDialog from '../DeleteDialog.vue'
import type { PlayList, Track } from './types'
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

import dataService from '@/services/dataService'
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

/**
 * Handle play playlist action from FilesList
 * @param {PlayList} playlist - Playlist to play
 */
const handlePlayPlaylist = async (playlist: PlayList) => {
  try {
    await dataService.startPlaylist(playlist.id)
    // Optionally, you may want to optimistically update UI or reload playlists
    // await loadPlaylists()
  } catch (err) {
    // Optionally show error to user
    console.error('Error starting playlist:', err)
  }
}

// Load playlists when component mounts
onMounted(loadPlaylists)
</script>
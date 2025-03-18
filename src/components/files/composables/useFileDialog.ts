// components/files/composables/useFilesDialog.ts
import { ref } from 'vue'
import type { Track, PlayList } from '../types'

export function useFileDialog() {
  const showDeleteDialog = ref(false)
  const selectedTrack = ref<Track | null>(null)
  const selectedPlaylist = ref<PlayList | null>(null)

  const openDeleteDialog = (track: Track, playlist: PlayList) => {
    selectedTrack.value = track
    selectedPlaylist.value = playlist
    showDeleteDialog.value = true
  }

  const closeDeleteDialog = () => {
    showDeleteDialog.value = false
    selectedTrack.value = null
    selectedPlaylist.value = null
  }

  return {
    showDeleteDialog,
    selectedTrack,
    selectedPlaylist,
    openDeleteDialog,
    closeDeleteDialog
  }
}
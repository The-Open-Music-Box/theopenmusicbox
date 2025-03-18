// components/files/FileListContainer.vue
<template>
  <div>
    <!-- Ajout de la gestion du chargement et des erreurs -->
    <div v-if="isLoading" class="text-gray-600">Chargement...</div>
    <div v-if="error" class="text-red-600">{{ error }}</div>
    
    <template v-if="!isLoading && !error">
      <FilesListHeader />
      <FilesList 
        :playlists="playlists"
        :selectedTrack="selectedTrack"
        @deleteTrack="handleDeleteTrack"
        @select-track="handleSelectTrack"
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
import { onMounted, ref, defineProps, defineEmits } from 'vue'
import { useFilesStore } from '../files/composables/useFilesStore'
import FilesListHeader from './FilesListHeader.vue'
import FilesList from './FilesList.vue'
import DeleteDialog from '../DeleteDialog.vue'
import type { PlayList, Track } from '../files/types'

const props = defineProps<{
  selectedTrack?: Track | null
}>()

const localSelectedTrack = ref<Track | null>(props.selectedTrack || null)

const emit = defineEmits<{
  (e: 'select-track', data: { track: Track, playlist: PlayList }): void
}>()

const { playlists, isLoading, error, loadPlaylists, deleteTrack } = useFilesStore()
const showDeleteDialog = ref(false)
const selectedPlaylist = ref<PlayList | null>(null)

const closeDeleteDialog = () => {
  showDeleteDialog.value = false
  selectedPlaylist.value = null
}

const handleSelectTrack = (data: { track: Track, playlist: PlayList }) => {
  emit('select-track', data)
}

const handleDeleteTrack = ({ playlistId, trackNumber }: { playlistId: string, trackNumber: number }) => {
  const playlist = playlists.value.find(p => p.id === playlistId)
  if (!playlist) return

  const track = playlist.tracks.find(t => t.number === trackNumber)
  if (!track) return

  selectedPlaylist.value = playlist
  showDeleteDialog.value = true
}

const handleDeleteConfirm = async () => {
  if (!localSelectedTrack.value || !selectedPlaylist.value) return
  try {
    await deleteTrack(selectedPlaylist.value.id, localSelectedTrack.value.number)
    closeDeleteDialog()
  } catch (err) {
    // L'erreur est déjà gérée dans le store
  }
}

onMounted(loadPlaylists)
</script>
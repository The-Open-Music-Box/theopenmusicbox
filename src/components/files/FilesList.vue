<template>
  <div class="mt-8 space-y-6">
    <!-- Edit mode toggle and controls -->
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-lg font-semibold text-onBackground">{{ t('file.playlists') }}</h2>
      <div class="flex gap-2">
        <button
          @click="toggleEditMode"
          :class="[
            'px-3 py-1.5 rounded-md text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-focus',
            isEditMode ? 'bg-success text-onSuccess' : 'bg-primary text-onPrimary hover:bg-primary-light'
          ]"
        >
          {{ isEditMode ? t('common.doneEditing') : t('common.edit') }}
        </button>
        <NewPlaylistButton
          v-if="isEditMode"
          @click="showCreatePlaylistDialog = true"
        />
      </div>
    </div>

    <!-- Error message -->
    <div v-if="error" :class="['text-error', 'py-4']">
      {{ error }}
    </div>

    <!-- Empty state message -->
    <div v-if="!error && (!playlists || playlists.length === 0)" class="flex flex-col items-center justify-center py-10 px-4 bg-surface border border-border rounded-lg">
      <div class="text-center mb-6">
        <h3 class="text-lg font-medium text-onBackground mb-2">{{ t('file.noPlaylistsYet') }}</h3>
        <p class="text-onBackground-medium">{{ t('file.createPlaylistPrompt') }}</p>
      </div>
      <NewPlaylistButton
        @click="showCreatePlaylistDialog = true"
      />
    </div>

    <!-- Playlists list -->
    <div v-for="playlist in playlists" :key="playlist.id" :class="['bg-surface', 'border border-border', 'rounded-lg overflow-hidden shadow-sm']">
      <!-- Playlist header (always visible) -->
      <div
        @click="!isEditMode && togglePlaylist(playlist.id)"
        :class="[`px-4 py-3 transition-colors flex justify-between items-center`, isEditMode ? '' : 'cursor-pointer', 'hover:bg-background']"
      >
        <div>
          <!-- Editable title in edit mode, regular title otherwise -->
          <div v-if="isEditMode" class="flex items-center">
            <input
              v-model="editableTitles[playlist.id]"
              @blur="updatePlaylistTitle(playlist.id)"
              @keyup.enter="updatePlaylistTitle(playlist.id)"
              class="text-sm font-semibold leading-6 bg-transparent border-b border-primary focus:border-success focus:outline-none px-1 py-0.5 w-full max-w-xs"
              :placeholder="t('file.playlistTitle')"
            />
          </div>
          <h3 v-else :class="['text-onBackground', 'text-sm font-semibold leading-6']">{{ playlist.title }}</h3>
          <p class="text-sm text-disabled">
            {{ playlist.tracks.length }} tracks • Total Duration: {{ formatTotalDuration(playlist.tracks) }} • Last Played: {{ playlist.last_played ? new Date(playlist.last_played).toLocaleDateString() : 'Never' }}
          </p>
        </div>
        <div class="flex items-center gap-2">
          <!-- Edit/Delete playlist buttons (only in edit mode) -->
          <div v-if="isEditMode" class="flex gap-2">
            <button
              @click.stop="confirmDeletePlaylist(playlist.id)"
              class="p-1.5 rounded-full bg-error hover:bg-error-light text-onError transition-colors focus:outline-none focus:ring-2 focus:ring-focus"
              :title="t('common.delete')"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>

          <!-- Play button without animation (hidden in edit mode) -->
          <button
            v-if="!isEditMode"
            @click.stop="$emit('play-playlist', playlist)"
            class="ml-1 h-10 w-10 flex items-center justify-center rounded-full transition-colors duration-150 focus:outline-none focus:ring-2"
            :class="playingPlaylistId === playlist.id ? 'bg-success' : 'bg-primary hover:bg-primary-light focus:ring-focus'"
            :title="playingPlaylistId === playlist.id ? (t('common.playing') || 'Playing') : (t('common.play') || 'Play this playlist')"
            type="button"
            aria-label="Play playlist"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-onPrimary" viewBox="0 0 24 24" fill="currentColor">
              <polygon points="8,5 8,19 19,12" />
            </svg>
          </button>

          <button
            v-if="!isEditMode"
            @click.stop="openNfcDialog(playlist.id)"
            :class="[
              'ml-1 p-2 rounded-full focus:outline-none focus:ring-2',
              playlist.nfc_tag_id ? 'bg-success hover:bg-success focus:ring-focus' : 'bg-primary hover:bg-primary-light focus:ring-focus'
            ]"
            :title="playlist.nfc_tag_id ? t('common.nfcLinkedTooltip') || 'Tag NFC associé à cette playlist' : t('common.linkNfc') || 'Associer un tag NFC'"
            type="button"
          >
            <svg v-if="playlist.nfc_tag_id" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-onPrimary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-onPrimary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17V7a5 5 0 00-10 0v10a5 5 0 0010 0zM7 17V7a5 5 0 0110 0v10a5 5 0 01-10 0z" />
            </svg>
          </button>
          <span v-if="!isEditMode" class="text-disabled">
            <svg
              class="w-6 h-6 transform transition-transform"
              :class="{ 'rotate-180': openPlaylists.includes(playlist.id) }"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </span>

        </div>
      </div>

      <!-- Enhanced chunked uploader (only in edit mode) -->
      <div v-if="isEditMode" class="px-4 py-2 border-t border-border bg-background-light">
        <EnhancedChunkedPlaylistUploader
          :playlist-id="playlist.id"
          @upload-complete="handleUploadComplete"
          @upload-error="handleUploadError"
          @all-uploads-complete="handleAllUploadsComplete"
        />
      </div>

      <!-- Upload Button (in edit mode only) -->
      <div v-if="isEditMode" class="upload-section">
        <button @click="openUploadModal(playlist.id)" class="btn-upload">
          <i class="fas fa-upload"></i>
          {{ t('file.uploadFiles') }}
        </button>
      </div>

      <!-- Tracks list (visible only if playlist is open) -->
      <div>
        <draggable
          v-model="playlist.tracks"
          :disabled="!isEditMode"
          group="tracks"
          item-key="number"
          :animation="200"
          ghost-class="bg-primary/10"
          chosen-class="bg-primary/5"
          drag-class="cursor-grabbing"
          :data-playlist-id="playlist.id"
          @start="dragStart"
          @end="dragEnd"
          @change="handleDragChange($event, playlist.id)"
        >
          <template #item="{element: track}">
            <div
              @click="isEditMode ? null : $emit('select-track', { track, playlist })"
              :class="[
                'px-4 py-3 flex items-center justify-between group',
                'hover:bg-background',
                isEditMode ? 'cursor-grab' : 'cursor-pointer'
              ]">
            <div class="flex items-center space-x-3">
              <div class="w-8 flex items-center justify-center">
                <!-- Track number or wavy icon if playing -->
                <span v-if="!(playingPlaylistId === playlist.id && playingTrackNumber === track.number)" :class="['text-success']">{{ track.number }}</span>
                <span v-else class="wavy-anim" title="Playing">
                  <svg width="16" height="16" viewBox="0 0 20 20" fill="none">
                    <rect x="2" y="6" width="2" height="8" rx="1" class="wavy-bar bar1"/>
                    <rect x="6" y="4" width="2" height="12" rx="1" class="wavy-bar bar2"/>
                    <rect x="10" y="7" width="2" height="6" rx="1" class="wavy-bar bar3"/>
                    <rect x="14" y="5" width="2" height="10" rx="1" class="wavy-bar bar4"/>
                  </svg>
                </span>
                <svg v-if="selectedTrack?.number === track.number && !(playingPlaylistId === playlist.id && playingTrackNumber === track.number)" :class="['text-disabled', 'h-5 w-5']" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" />
                </svg>
              </div>
              <div>
                <p :class="['text-onBackground', 'font-medium']">{{ track.title }}</p>
              </div>
            </div>

            <div class="flex items-center space-x-4">
              <span :class="['text-success']">{{ formatDuration(track.duration) }}</span>
              <button v-if="isEditMode" @click.stop="$emit('deleteTrack', { playlistId: playlist.id, trackNumber: track.number })"
                      class="text-disabled hover:text-error transition-colors opacity-0 group-hover:opacity-100 delete-dialog-buttons">
                <span class="sr-only">{{ t('common.delete') }}</span>
                <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          </div>
          </template>
        </draggable>
      </div>
    </div>
    <!-- NFC Association Dialog -->
    <NfcAssociateDialog
      :open="showNfcDialog"
      :playlistId="selectedPlaylistId"
      @success="handleNfcSuccess"
      @close="showNfcDialog = false"
    />

    <!-- Delete Confirmation Dialog -->
    <DeleteDialog
      :open="showDeleteDialog"
      :title="t('file.deletePlaylistTitle')"
      :message="t('file.deletePlaylistMessage')"
      @confirm="deletePlaylist"
      @cancel="showDeleteDialog = false"
    />

    <!-- Create Playlist Dialog -->
    <CreatePlaylistDialog
      :open="showCreatePlaylistDialog"
      @create="createNewPlaylist"
      @cancel="showCreatePlaylistDialog = false"
    />

    <!-- Upload Modal -->
    <UploadModal v-if="currentUploadPlaylistId" :playlist-id="currentUploadPlaylistId" />

    <!-- Feedback toast message -->
    <transition
      enter-active-class="transform transition ease-out duration-300"
      enter-from-class="translate-y-2 opacity-0 sm:translate-y-0 sm:translate-x-2"
      enter-to-class="translate-y-0 opacity-100 sm:translate-x-0"
      leave-active-class="transition ease-in duration-200"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="feedbackMessage"
        :class="[
          'fixed bottom-4 right-4 px-4 py-3 rounded-lg shadow-lg z-50 max-w-sm',
          feedbackType === 'success' ? 'bg-success text-onSuccess' : 'bg-error text-onError'
        ]"
      >
        <div class="flex items-center">
          <svg v-if="feedbackType === 'success'" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
          <svg v-else class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{{ feedbackMessage }}</span>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { colors } from '@/theme/colors'

import { ref, computed, nextTick, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import type { PlayList, Track } from './types'
import dataService from '@/services/dataService'
import NfcAssociateDialog from './NfcAssociateDialog.vue'
import DeleteDialog from './DeleteDialog.vue'
import CreatePlaylistDialog from './CreatePlaylistDialog.vue'
import UploadModal from '@/components/upload/UploadModal.vue'
import { useUploadModalStore } from '@/stores/uploadModalStore'
import draggable from 'vuedraggable'

const { t } = useI18n()
const uploadModalStore = useUploadModalStore()

const props = defineProps<{
  playlists: PlayList[];
  error?: string;
  selectedTrack?: Track | null;
  playingPlaylistId?: string | null;
  playingTrackNumber?: number | null;
}>()

const emit = defineEmits(['refreshPlaylists', 'play-playlist', 'select-track', 'deleteTrack', 'feedback'])

// Listen for feedback event from parent
function onFeedback({ type, message }: { type: 'success' | 'error', message: string }) {
  showFeedback(type, message)
}

// Edit mode state
// Force le mode édition à false au démarrage du composant
const isEditMode = ref(false)
// Simple local toggle for edit mode
const toggleEditMode = () => {
  isEditMode.value = !isEditMode.value
  console.log('[FilesList] Edit mode toggled to:', isEditMode.value)
}

// Editable titles for playlists
const editableTitles = ref<Record<string, string>>({})

// Initialize editable titles when playlists change
watch(() => props.playlists, (newPlaylists) => {
  newPlaylists.forEach(playlist => {
    if (!editableTitles.value[playlist.id]) {
      editableTitles.value[playlist.id] = playlist.title
    }
  })
}, { immediate: true })

// Delete dialog state
const showDeleteDialog = ref(false)
const playlistToDelete = ref<string | null>(null)

// Create playlist dialog state
const showCreatePlaylistDialog = ref(false)

// Upload modal state
const currentUploadPlaylistId = ref<string | null>(null)

// Drag and drop state
const draggedTrack = ref<Track | null>(null)
const dragSourcePlaylistId = ref<string | null>(null)
const dragTargetPlaylistId = ref<string | null>(null)

// Feedback messages
const feedbackMessage = ref('')
const feedbackType = ref<'success' | 'error' | ''>('')
const feedbackTimeout = ref<number | null>(null)

// Initialize with empty playlist ids (all playlists closed by default)
const openPlaylists = ref<string[]>([])

// No auto-open behavior needed, playlists will be closed by default
onMounted(() => {
  // Initialized with empty array - all playlists closed
  // Playlists initialized in closed state by default
})

// Update open playlists when the playlist list changes
watch(() => props.playlists, (newPlaylists) => {
  // Add any new playlists to openPlaylists
  if (newPlaylists && newPlaylists.length > 0) {
    const currentIds = openPlaylists.value
    const newIds = newPlaylists.map(p => p.id).filter(id => !currentIds.includes(id))
    if (newIds.length > 0) {
      openPlaylists.value = [...currentIds, ...newIds]
    }
  }
}, { deep: true })

// NFC dialog state and logic
const showNfcDialog = ref(false)
const selectedPlaylistId = ref<string | null>(null)

/**
 * Handle successful NFC tag association
 * Refresh playlists but don't close the dialog automatically
 * @param {Object} data - Optional data from the success event
 */
const handleNfcSuccess = (data: any) => {
  // Emit refresh but don't close dialog unless specified
  emit('refreshPlaylists')
  // Only close dialog if explicitly requested
  if (data && data.closeDialog === true) {
    showNfcDialog.value = false
  }
  // Otherwise, leave dialog open for user to close manually
}

function openNfcDialog(id: string) {
  selectedPlaylistId.value = id
  showNfcDialog.value = true
}

/**
 * Update a playlist title after editing
 * @param {string} playlistId - Playlist identifier
 */
async function updatePlaylistTitle(playlistId: string) {
  const newTitle = editableTitles.value[playlistId]?.trim()
  if (!newTitle) return

  try {
    await dataService.updatePlaylist(playlistId, { title: newTitle })
    emit('refreshPlaylists')
    showFeedback('success', t('file.playlistUpdated'))
  } catch (error) {
    showFeedback('error', t('file.errorUpdating'))
    console.error('Error updating playlist title:', error)
  }
}

/**
 * Show delete confirmation dialog for a playlist
 * @param {string} playlistId - Playlist identifier
 */
function confirmDeletePlaylist(playlistId: string) {
  playlistToDelete.value = playlistId
  showDeleteDialog.value = true
}

/**
 * Delete a playlist after confirmation
 */
async function deletePlaylist() {
  if (!playlistToDelete.value) return

  try {
    // Here you would call a method to delete the playlist
    // await filesStore.deletePlaylist(playlistToDelete.value)
    console.log('[FilesList] Playlist deleted:', playlistToDelete.value)
    emit('refreshPlaylists')
    showFeedback('success', t('file.playlistDeleted'))
  } catch (err) {
    console.error('[FilesList] Error deleting playlist:', err)
    // Reload playlists to reset the UI state
    emit('refreshPlaylists')
  } finally {
    showDeleteDialog.value = false
    playlistToDelete.value = null
  }
}

/**
 * Create new playlist and put it in edit mode
 * @param {string} title - Title for the new playlist
 */
async function createNewPlaylist(title: string) {
  try {
    console.log('[FilesList] Creating new playlist:', title)

    // Créer la nouvelle playlist
    const newPlaylistId = await dataService.createPlaylist({ title })
    console.log('[FilesList] Playlist created successfully with ID:', newPlaylistId)

    showCreatePlaylistDialog.value = false
    showFeedback('success', t('file.playlistCreated'))

    // Store current edit mode state before refresh (smart refresh logic)
    const wasInEditMode = isEditMode.value
    console.log('[FilesList] Smart refresh after playlist creation: preserving edit mode =', wasInEditMode)

    // Activer le mode édition si ce n'est pas déjà fait
    if (!isEditMode.value) {
      // Activate edit mode
      isEditMode.value = true // Activer le mode édition localement
    }

    // CRITICAL FIX: Refresh playlists directly after creation
    console.log('[FilesList] Calling loadPlaylists directly after playlist creation')
    emit('refreshPlaylists')
    
    // Also try to refresh via the files store directly as backup
    try {
      emit('refreshPlaylists')
      console.log('[FilesList] Direct loadPlaylists completed successfully')
    } catch (err) {
      console.error('[FilesList] Error during direct loadPlaylists:', err)
    }

    // After refresh, ensure edit mode and playlist state are preserved
    nextTick(() => {
      console.log('[FilesList] Smart refresh after playlist creation: restoring state')

      // Ensure edit mode is preserved after refresh
      if (!isEditMode.value && (wasInEditMode || newPlaylistId)) {
        console.log('[FilesList] Restoring edit mode after playlist creation refresh')
        isEditMode.value = true
      }

      // Add to open playlists and ensure the new playlist is opened in edit mode
      if (newPlaylistId && !openPlaylists.value.includes(newPlaylistId)) {
        console.log('[FilesList] Opening newly created playlist in edit mode:', newPlaylistId)
        openPlaylists.value.push(newPlaylistId)
      }
    })
  } catch (err) {
    console.error('Error creating playlist:', err)
    showFeedback('error', t('file.errorCreating'))
  }
}

/**
 * Show feedback toast message
 * @param {string} type - Message type (success/error)
 * @param {string} message - Message to display
 */
function showFeedback(type: 'success' | 'error', message: string) {
  // Clear any existing timeout
  if (feedbackTimeout.value) {
    clearTimeout(feedbackTimeout.value)
  }

  // Set message and type
  feedbackType.value = type
  feedbackMessage.value = message

  // Auto-hide after 3 seconds
  feedbackTimeout.value = window.setTimeout(() => {
    feedbackMessage.value = ''
    feedbackType.value = ''
    feedbackTimeout.value = null
  }, 3000)
}

/**
 * Handle drag start event
 * @param {Event} evt - Drag event
 */
function dragStart(evt: any) {
  draggedTrack.value = evt.item
  dragSourcePlaylistId.value = evt.from.dataset.playlistId || null
  console.log('[FilesList] Drag started from playlist:', dragSourcePlaylistId.value)
}

/**
 * Handle drag end event
 * @param {Event} evt - Drag event
 */
function dragEnd(evt: any) {
  draggedTrack.value = null
  dragSourcePlaylistId.value = null
  dragTargetPlaylistId.value = null
}

/**
 * Handle drag change event (added, removed, moved)
 * @param {Event} evt - Change event
 * @param {string} playlistId - Current playlist ID
 */
async function handleDragChange(evt: any, playlistId: string) {
  console.log('[FilesList] Drag change event:', evt.added ? 'added' : evt.removed ? 'removed' : 'moved', 'in playlist:', playlistId)

  // Handle reordering within the same playlist
  if (evt.moved) {
    try {
      // Get the new order of track numbers
      const trackNumbers = props.playlists
        .find(p => p.id === playlistId)?.tracks
        .map(track => track.number) || []

      // Call the API to update the order
      await dataService.reorderTracks(playlistId, trackNumbers)
      console.log('[FilesList] Tracks reordered in playlist:', playlistId)
      showFeedback('success', t('file.tracksReordered'))
    } catch (err) {
      console.error('[FilesList] Error reordering tracks:', err)
      // Reload playlists to reset the UI state
      emit('refreshPlaylists')
    }
    return
  }

  // Handle moving between playlists
  if (evt.added && evt.from) {
    const sourcePlaylistId = evt.from.dataset.playlistId
    if (sourcePlaylistId && sourcePlaylistId !== playlistId) {
      try {
        const movedTrack = evt.added.element
        console.log('[FilesList] Track moved between playlists:', movedTrack.number, 'from', sourcePlaylistId, 'to', playlistId)

        // Call the API to move the track
        await dataService.moveTrackBetweenPlaylists(
          sourcePlaylistId,
          playlistId,
          movedTrack.number
        )
        showFeedback('success', t('file.trackMoved'))
      } catch (err) {
        // Log error but continue execution
        // Reload playlists to reset the UI state
        emit('refreshPlaylists')
      }
    }
  }
}

/**
 * Toggle a playlist's expanded/collapsed state
 * @param {string} playlistId - Playlist identifier
 */
function togglePlaylist(playlistId: string) {
  const index = openPlaylists.value.indexOf(playlistId)
  if (index === -1) {
    openPlaylists.value.push(playlistId)

  } else {
    openPlaylists.value.splice(index, 1)

  }
}

/**
 * Handle upload completion from enhanced uploader
 * Uses NO refresh to prevent interrupting multi-file uploads
 */
function handleUploadComplete() {
  console.log('[FilesList] Enhanced upload completed successfully')

  // DO NOT emit refreshPlaylists to prevent page refresh that breaks multi-file uploads
  // The playlist will be updated via optimistic updates or manual refresh when needed
  // This preserves UI state and allows multiple files to upload consecutively

  showFeedback('success', t('file.uploadSuccess'))
}

/**
 * Handle completion of ALL uploads for a playlist
 * This triggers a smart refresh to update the playlist with all uploaded tracks
 * while preserving the edit mode state
 */
function handleAllUploadsComplete(playlistId: string) {
  console.log('[FilesList] All uploads completed for playlist', playlistId)

  // Store the current edit mode state before refresh
  const wasInEditMode = isEditMode.value

  console.log('[FilesList] Smart refresh: preserving edit mode =', wasInEditMode, 'for playlist', playlistId)

  // Emit refresh to update the playlist with newly uploaded tracks
  emit('refreshPlaylists')

  // After refresh, restore the edit mode if it was active
  // Use nextTick to ensure DOM is updated after the refresh
  nextTick(() => {
    if (wasInEditMode) {
      console.log('[FilesList] Smart refresh: restoring edit mode for playlist', playlistId)
      // Re-enable edit mode after refresh
      isEditMode.value = true
    }

    showFeedback('success', t('file.uploadSuccess'))
  })
}

/**
 * Handle upload error from enhanced uploader
 * @param {any} error - Upload error details
 */
function handleUploadError(error: any) {
  console.error('[FilesList] Enhanced upload error:', error)
  showFeedback('error', t('file.uploadError'))
}

/**
 * Open upload modal for a playlist
 * @param {string} playlistId - Playlist identifier
 */
function openUploadModal(playlistId: string) {
  currentUploadPlaylistId.value = playlistId
  uploadModalStore.open(playlistId)
}

// Watch for modal close to refresh playlists
watch(() => uploadModalStore.isOpen(), (isOpen) => {
  if (!isOpen && currentUploadPlaylistId.value) {
    // Modal closed, refresh playlists
    emit('refreshPlaylists')
    currentUploadPlaylistId.value = null
  }
})

/**
 * Formats duration in seconds to MM:SS format
 * @param {string} duration - Duration in seconds as string
 * @returns {string} Formatted duration
 */
function formatDuration(duration: string): string {
  const seconds = parseInt(duration)
  if (isNaN(seconds)) return '00:00'
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`
}

/**
 * Computes and formats the total duration of all tracks in a playlist.
 * @param {Track[]} tracks
 * @returns {string} Formatted total duration (e.g., 1h12m or MM:SS)
 */
function formatTotalDuration(tracks: Track[]): string {
  if (!tracks || tracks.length === 0) return '00:00'
  let totalSeconds = 0
  for (const track of tracks) {
    // Accept both string and number durations
    const sec = typeof track.duration === 'number' ? track.duration : parseInt(track.duration)
    if (!isNaN(sec) && sec > 0) totalSeconds += sec
  }
  if (totalSeconds === 0) return '00:00'
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const seconds = totalSeconds % 60
  if (hours > 0) {
    return `${hours}h${minutes.toString().padStart(2, '0')}m`
  } else {
    return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
  }
}
</script>

<style scoped>

</style>


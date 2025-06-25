<template>
  <div class="mt-8 space-y-6">

    <!-- Error message -->
    <div v-if="error" :class="['text-error', 'py-4']">
      {{ error }}
    </div>

    <!-- Playlists list -->
    <div v-for="playlist in playlists" :key="playlist.id" :class="['bg-surface', 'border border-border', 'rounded-lg overflow-hidden shadow-sm']">
      <!-- Playlist header (always visible) -->
      <div
        @click="togglePlaylist(playlist.id)"
        :class="[`px-4 py-3 cursor-pointer transition-colors flex justify-between items-center`, 'hover:bg-background']"
      >
        <div>
          <h3 :class="['text-onBackground', 'text-sm font-semibold leading-6']">{{ playlist.title }}</h3>
          <p class="text-sm text-disabled">
            {{ playlist.tracks.length }} tracks • Total Duration: {{ formatTotalDuration(playlist.tracks) }} • Last Played: {{ playlist.last_played ? new Date(playlist.last_played).toLocaleDateString() : 'Never' }}
          </p>
        </div>
        <div class="flex items-center gap-2">

          <!-- Play button without animation -->
          <button
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
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17V7a5 5 0 00-10 0v10a5 5 0 0010 0zm-5 2a2 2 0 002-2H9a2 2 0 002 2z" />
            </svg>
          </button>
          <span class="text-disabled">
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

      <!-- Tracks list (visible only if playlist is open) -->
      <transition
        enter-active-class="transition-all duration-500 ease-out"
        leave-active-class="transition-all duration-300 ease-in"
        enter-from-class="max-h-0 opacity-0"
        enter-to-class="max-h-[1000px] opacity-100"
        leave-from-class="max-h-[1000px] opacity-100"
        leave-to-class="max-h-0 opacity-0"
      >
        <div v-show="openPlaylists.includes(playlist.id)" :class="['divide-y divide-border', 'overflow-hidden']">
          <div v-for="track in playlist.tracks" :key="track.number"
               @click="$emit('select-track', { track, playlist })"
               :class="['px-4 py-3 flex items-center justify-between cursor-pointer group', 'hover:bg-background']">
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
              <button @click.stop="$emit('deleteTrack', { playlistId: playlist.id, trackNumber: track.number })"
                      class="text-disabled hover:text-error transition-colors opacity-0 group-hover:opacity-100">
                <span class="sr-only">{{ t('common.delete') }}</span>
                <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </transition>
    </div>
    <!-- NFC Association Dialog -->
    <NfcAssociateDialog
      :open="showNfcDialog"
      :playlistId="selectedPlaylistId"
      @success="handleNfcSuccess"
      @close="showNfcDialog = false"
    />
  </div>
</template>

<script setup lang="ts">
import { colors } from '@/theme/colors'

import { ref } from 'vue'
import type { PlayList, Track } from './types'
import { useI18n } from 'vue-i18n'
import NfcAssociateDialog from './NfcAssociateDialog.vue'

const { t } = useI18n()

defineProps<{
  playlists: PlayList[];
  error?: string;
  selectedTrack?: Track | null;
  playingPlaylistId?: string | null;
  playingTrackNumber?: number | null;
}>()

const emit = defineEmits(['refreshPlaylists', 'play-playlist', 'select-track', 'deleteTrack'])


const openPlaylists = ref<string[]>([])

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
 * Toggle a playlist's expanded/collapsed state
 * @param {string} playlistId - Playlist identifier
 */
function togglePlaylist(playlistId: string) {
  const index = openPlaylists.value.indexOf(playlistId)
  if (index === -1) {
    openPlaylists.value.push(playlistId)
    console.log('[FilesList] Playlist opened:', playlistId)
  } else {
    openPlaylists.value.splice(index, 1)
    console.log('[FilesList] Playlist closed:', playlistId)
  }
}

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


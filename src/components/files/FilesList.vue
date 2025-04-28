<template>
  <div class="mt-8 space-y-6">

    <!-- Error message -->
    <div v-if="error" :class="[colors.error.main, 'text-center py-2']">
      {{ error }}
    </div>

    <!-- Playlists list -->
    <div v-for="playlist in playlists" :key="playlist.id" class="bg-gray-800 rounded-lg overflow-hidden">
      <!-- Playlist header (always visible) -->
      <div
        @click="togglePlaylist(playlist.id)"
        class="px-4 py-3 cursor-pointer hover:bg-gray-700 transition-colors flex justify-between items-center"
      >
        <div>
          <h3 :class="[colors.text.white, 'text-lg font-medium']">{{ playlist.title }}</h3>
          <p class="text-sm text-gray-400">
            {{ playlist.tracks.length }} {{ $t('file.tracks') }} • {{ $t('file.lastPlayed') }}: {{ new Date(playlist.last_played).toLocaleDateString() }}
          </p>
        </div>
        <div class="flex items-center gap-2">
        <button
            @click.stop="onPlaylistAction(playlist.id)"
            class="ml-2 px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded shadow focus:outline-none focus:ring-2 focus:ring-blue-400"
            type="button"
            :title="$t('common.linkNfcTooltip') || 'Associate an NFC tag with a selected playlist for quick access.'"
          >
            {{$t('common.link') || 'Link'}}
          </button>
          <span class="text-gray-400">
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
        <div v-show="openPlaylists.includes(playlist.id)" class="divide-y divide-gray-700 overflow-hidden">
          <div v-for="track in playlist.tracks" :key="track.number"
               @click="$emit('select-track', { track, playlist })"
               class="px-4 py-3 flex items-center justify-between hover:bg-gray-700 cursor-pointer group">
            <div class="flex items-center space-x-3">
              <div class="w-8 flex items-center justify-center">
                <span v-if="selectedTrack?.number !== track.number" :class="[colors.secondary.main]">{{ track.number }}</span>
                <svg v-else :class="[colors.text.secondary, 'h-5 w-5']" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" />
                </svg>
              </div>
              <div>
                <p :class="[colors.text.white, 'font-medium']">{{ track.title }}</p>
                <p class="text-sm text-gray-400">{{ track.filename }}</p>
              </div>
            </div>

            <div class="flex items-center space-x-4">
              <span :class="[colors.secondary.main]">{{ formatDuration(track.duration) }}</span>
              <button @click.stop="$emit('deleteTrack', { playlistId: playlist.id, trackNumber: track.number })"
                      class="text-gray-400 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100">
                <span class="sr-only">{{ $t('common.delete') }}</span>
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
  </div>
  <!-- NFC Link Dialog -->
  <div v-if="showNfcDialog" class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
    <div class="bg-white rounded-lg shadow-lg max-w-md w-full p-6">
      <h2 class="text-lg font-semibold mb-4 text-gray-900 flex items-center">
        <svg class="w-5 h-5 mr-2 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m4 4h1a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v7a2 2 0 002 2h1" /></svg>
        {{ $t('common.linkNfcTitle') || 'Associate NFC Tag' }}
      </h2>
      <div v-if="!nfcLinked && !nfcError" class="flex flex-col items-center">
        <span class="mb-2 text-gray-700">{{$t('common.awaitingNfc') || 'Awaiting NFC tag...'}} </span>
        <svg class="animate-spin h-8 w-8 text-blue-500 mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path>
        </svg>
      </div>
      <div v-if="nfcLinked" class="flex flex-col items-center">
        <span class="mb-2 text-green-700 font-semibold">{{$t('common.nfcLinkedMsg') || 'NFC tag successfully linked to playlist!'}} </span>
        <svg class="h-8 w-8 text-green-500 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
      </div>
      <div v-if="nfcError" class="flex flex-col items-center">
        <span class="mb-2 text-red-700 font-semibold">{{$t('common.nfcLinkError') || 'Failed to link NFC tag.'}} </span>
      </div>
      <div class="flex justify-end space-x-2 mt-6">
        <button @click="closeNfcDialog" class="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300">{{ $t('common.close') || 'Close' }}</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">

import { ref } from 'vue'
import type { PlayList, Track } from '../files/types'
import { i18n } from '@/i18n'
import { colors } from '@theme/colors'
import socketService from '@/services/socketService'

const { t: $t } = i18n

defineProps<{
  playlists: PlayList[];
  error?: string;
  selectedTrack?: Track | null;
}>()

defineEmits<{
  (e: 'deleteTrack', data: { playlistId: string, trackNumber: number }): void;
  (e: 'select-track', data: { track: Track, playlist: PlayList }): void;
}>()

const openPlaylists = ref<string[]>([])

// NFC dialog state and logic
const showNfcDialog = ref(false)
const selectedPlaylistId = ref<string | null>(null)
const nfcLinked = ref(false)
const nfcError = ref(false)
// Use ReturnType<typeof window["io"]> if available, otherwise fallback to 'any'.
// socketService will be used for all NFC socket actions

function onPlaylistAction(id: string) {
  console.log('[FilesList] Link button clicked for playlist:', id)
  selectedPlaylistId.value = id
  showNfcDialog.value = true
  nfcLinked.value = false
  nfcError.value = false
  startNfcAssociation(id)
}

function closeNfcDialog() {
  console.log('[FilesList] NFC dialog closed')
  showNfcDialog.value = false
  selectedPlaylistId.value = null
  nfcLinked.value = false
  nfcError.value = false
  // Nettoie les listeners NFC
  socketService.off('nfc_linked')
  socketService.off('nfc_error')
}

function startNfcAssociation(playlistId: string) {
  console.log('[FilesList] Starting NFC association for playlist:', playlistId)
  // Utilise socketService pour la communication NFC
  socketService.emit('start_nfc_link', { playlist_id: playlistId })
  socketService.on('nfc_linked', () => {
    console.log('[FilesList] NFC tag successfully linked to playlist:', playlistId)
    nfcLinked.value = true;
  })
  socketService.on('nfc_error', (err: unknown) => {
    console.error('[FilesList] NFC link error:', err)
    nfcError.value = true;
  })
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
</script>

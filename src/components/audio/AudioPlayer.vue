<template>
  <div class="flex items-center justify-center">
    <div class="w-2/3">
      <div class="bg-white border-slate-100 dark:bg-slate-800 dark:border-slate-500 border-b rounded-t-xl p-4 pb-6 sm:p-10 sm:pb-8 lg:p-6 xl:p-10 xl:pb-8 space-y-6 sm:space-y-8 lg:space-y-6 xl:space-y-8 items-center">
        <TrackInfo :track="currentTrack || undefined" />
        <ProgressBar
          :currentTime="currentTime"
          :duration="duration"
        />
      </div>
      <div class="bg-slate-50 text-slate-500 dark:bg-slate-600 dark:text-slate-200 rounded-b-xl flex items-center">
        <PlaybackControls
          :isPlaying="isPlaying"
          @toggle-play-pause="togglePlayPause"
          @previous="previous"
          @next="next"
          @rewind="rewind"
          @skip="skip"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * AudioPlayer Component
 *
 * A full-featured audio player with:
 * - Play/Pause functionality
 * - Track progress visualization
 * - Next/Previous track navigation
 * - Skip forward/backward controls
 * - Track metadata display
 */
import { ref, onMounted, onUnmounted } from 'vue'
import TrackInfo from './TrackInfo.vue'
import ProgressBar from './ProgressBar.vue'
import PlaybackControls from './PlaybackControls.vue'
import type { Track, PlayList } from '../files/types'
import socketService from '@/services/socketService'
import apiService from '@/services/realApiService'

// Component props with types and defaults
interface Props {
  /** The currently selected track */
  selectedTrack?: Track | null;
  /** The playlist containing the track */
  playlist?: PlayList | null;
}

const props = withDefaults(defineProps<Props>(), {
  selectedTrack: null,
  playlist: null
})

// State management
const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const currentTrack = ref<Track | null>(null)
const currentPlaylist = ref<PlayList | null>(null)

// Listen for WebSocket events
let lastBackendTime = 0
let lastReceivedTimestamp = 0
let progressInterval: ReturnType<typeof setInterval> | null = null

function startProgressTimer() {
  console.log('[AudioPlayer] startProgressTimer called. isPlaying:', isPlaying.value, 'duration:', duration.value, 'at', Date.now());
  if (progressInterval) clearInterval(progressInterval)
  progressInterval = setInterval(() => {
    // Log à chaque tick d'update progress bar
    if (isPlaying.value && duration.value > 0) {
     // console.log('[AudioPlayer] ProgressBar Tick. isPlaying:', isPlaying.value, 'currentTime:', currentTime.value, 'duration:', duration.value, 'at', Date.now());
      const now = Date.now() / 1000
      const elapsed = now - lastReceivedTimestamp
      const displayTime = Math.min(lastBackendTime + elapsed, duration.value)
      currentTime.value = displayTime
    } else {
      // Stop timer if not playing
      if (progressInterval) {
        clearInterval(progressInterval)
        progressInterval = null
        console.log('[AudioPlayer] Progress timer stopped (paused or no duration) at', Date.now());
      }
    }
  }, 200)
}

import { watch } from 'vue'

onMounted(() => {
  console.log('[AudioPlayer] onMounted at', Date.now());
  socketService.on('track_progress', (data: any) => {
    console.log('[AudioPlayer] Received backend track_progress:', data, 'at', Date.now());
    // data: { track, playlist, current_time, duration, is_playing }
    currentTrack.value = data.track
    currentPlaylist.value = data.playlist
    lastBackendTime = data.current_time
    lastReceivedTimestamp = Date.now() / 1000
    duration.value = data.duration
    isPlaying.value = data.is_playing // Always sync from backend
    // Set currentTime immediately to backend value
    currentTime.value = lastBackendTime
    // Timer will be managed by watcher
  })
  socketService.on('playback_status', (data: any) => {
    console.log('[AudioPlayer] Received backend playback_status:', data, 'at', Date.now());
    // data: { status, playlist, current_track }
    currentTrack.value = data.current_track || null
    currentPlaylist.value = data.playlist || null
    // Optionally map status to isPlaying
    isPlaying.value = data.status === 'playing' // Always sync from backend
    // duration and currentTime may not be present; set to 0 if missing
    duration.value = data.current_track?.duration || 0
    currentTime.value = 0 // Or keep previous if you want to preserve progress
    // Timer will be managed by watcher
  })
  socketService.on('connection_status', (data: any) => {
    // Optionally handle connection status changes
  })
  socketService.setupSocketConnection()
})

onUnmounted(() => {
  socketService.off('track_progress')
  socketService.off('playback_status')
  socketService.off('connection_status')
  if (progressInterval) clearInterval(progressInterval)
})

// Watcher pour gérer le timer selon l'état lecture/pause
watch(isPlaying, (newVal) => {
  if (newVal) {
    startProgressTimer()
  } else if (progressInterval) {
    clearInterval(progressInterval)
    progressInterval = null
    console.log('[AudioPlayer] Progress timer stopped by watcher (paused) at', Date.now());
  }
})

const togglePlayPause = async () => {
  console.log('[AudioPlayer] Play/Pause button clicked. isPlaying before:', isPlaying.value, 'at', Date.now());
  if (!currentTrack.value) return
  const action = isPlaying.value ? 'pause' : 'resume'
  console.log('[AudioPlayer] Sending controlPlaylist action:', action, 'at', Date.now());
  // Optimistic UI update for immediate feedback
  isPlaying.value = !isPlaying.value;
  await apiService.controlPlaylist(action)
  // The real value will be resynced on backend event
}

const rewind = () => {
  // Not supported in monitor mode
}

const skip = () => {
  // Not supported in monitor mode
}

const previous = async () => {
  console.log('[AudioPlayer] Previous button clicked at', Date.now());
  await apiService.controlPlaylist('previous')
}

const next = async () => {
  console.log('[AudioPlayer] Next button clicked at', Date.now());
  await apiService.controlPlaylist('next')
}
</script>
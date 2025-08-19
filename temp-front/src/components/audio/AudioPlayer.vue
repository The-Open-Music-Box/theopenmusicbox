<template>
  <div class="w-full max-w-xl mx-auto">
    <div :class="['bg-surface', 'border-border', 'border-b rounded-t-xl p-4 pb-6 sm:p-10 sm:pb-8 lg:p-6 xl:p-10 xl:pb-8 space-y-6 sm:space-y-8 lg:space-y-6 xl:space-y-8 items-center']">
      <TrackInfo :track="currentTrack || undefined" />
      <ProgressBar
        :currentTime="currentTime"
        :duration="duration"
      />
    </div>
    <div :class="['bg-background', 'text-disabled', 'rounded-b-xl flex items-center justify-center w-full']">
      <div class="w-full max-w-[380px] mx-auto flex justify-center">
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
import { ref, onMounted, onUnmounted, watch } from 'vue'
import TrackInfo from './TrackInfo.vue'
import ProgressBar from './ProgressBar.vue'
import PlaybackControls from './PlaybackControls.vue'
import type { Track, PlayList } from '../files/types'
import socketService from '@/services/socketService'
import apiService from '@/services/realApiService'
import { logger } from '@/utils/logger'

// Component props with types and defaults
interface Props {
  /** The currently selected track */
  selectedTrack?: Track | null;
  /** The playlist containing the track */
  playlist?: PlayList | null;
}

withDefaults(defineProps<Props>(), {
  selectedTrack: null,
  playlist: null
})

// State management
const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const currentTrack = ref<Track | null>(null)
const currentPlaylist = ref<PlayList | null>(null)
// Loading state for track change
const isChangingTrack = ref(false)

// Listen for WebSocket events
let lastBackendTime = 0
let lastReceivedTimestamp = 0

let progressInterval: ReturnType<typeof setInterval> | null = null

function startProgressTimer() {
  logger.debug('Starting progress timer', { isPlaying: isPlaying.value, duration: duration.value }, 'AudioPlayer');
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
        logger.debug('Progress timer stopped (paused or no duration)', {}, 'AudioPlayer');
      }
    }
  }, 200)
}

onMounted(() => {
  logger.debug('AudioPlayer mounted', {}, 'AudioPlayer');
  socketService.on('track_progress', (data: unknown) => {
    try {
      const trackData = data as { track?: Track; playlist?: PlayList; current_time?: number; duration?: number; is_playing?: boolean }
      logger.debug('Received track_progress', { trackData }, 'AudioPlayer');
      // data: { track, playlist, current_time, duration, is_playing }
      // Detect track change
      const isNewTrack = currentTrack.value?.filename !== trackData.track?.filename
      if (isChangingTrack.value && isNewTrack) {
        isChangingTrack.value = false;
        // Resume playback and reset progress bar
        isPlaying.value = true;
        currentTime.value = 0;
      }
      currentTrack.value = trackData.track || null;
      currentPlaylist.value = trackData.playlist || null;
      lastBackendTime = trackData.current_time || 0;
      lastReceivedTimestamp = Date.now() / 1000;
      duration.value = trackData.duration || 0;
      // Always sync from backend, but only auto-resume if this was a track change
      if (!isChangingTrack.value) {
        isPlaying.value = trackData.is_playing || false;
      }
      // Set currentTime immediately to backend value or reset if new track
      if (!isChangingTrack.value) {
        currentTime.value = isNewTrack ? 0 : lastBackendTime;
      }
      // Timer will be managed by watcher
    } catch (err) {
      logger.error('Error updating playback state from track_progress', { error: err, data }, 'AudioPlayer');
    }
  })
  socketService.on('playback_status', (data: unknown) => {
    try {
      const statusData = data as { status?: string; playlist?: PlayList; current_track?: Track }
      logger.debug('Received playback_status', { statusData }, 'AudioPlayer');
      // data: { status, playlist, current_track }
      // Detect track change
      const isNewTrack = currentTrack.value?.filename !== statusData.current_track?.filename
      currentTrack.value = statusData.current_track || null
      currentPlaylist.value = statusData.playlist || null
      // Optionally map status to isPlaying
      isPlaying.value = statusData.status === 'playing' // Always sync from backend
      // duration and currentTime may not be present; set to 0 if missing
      duration.value = statusData.current_track?.duration ? parseInt(statusData.current_track.duration) : 0
      currentTime.value = isNewTrack ? 0 : currentTime.value
      // Timer will be managed by watcher
    } catch (err) {
      logger.error('Error updating playback state from playback_status', { error: err, data }, 'AudioPlayer');
    }
  })
  socketService.on('connection_status', (data: unknown) => {
    const connectionData = data as { status?: string }
    // Handle connection status changes, especially reconnection
    if (connectionData.status === 'connected') {
      // Request current playback status to resync state
      try {
        socketService.emit && socketService.emit('get_playback_status', {});
        logger.debug('Requested playback status after reconnect', {}, 'AudioPlayer');
      } catch (err) {
        logger.error('Error requesting playback status after reconnect', { error: err }, 'AudioPlayer');
      }
    }
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
    logger.debug('Progress timer stopped by watcher (paused)', {}, 'AudioPlayer');
  }
})

const togglePlayPause = async () => {
  const action = isPlaying.value ? 'pause' : 'resume';
  logger.debug('Play/Pause button clicked', { action, wasPlaying: isPlaying.value }, 'AudioPlayer');
  try {
    // Ne pas faire de mise à jour optimiste !
    await apiService.controlPlaylist(action);
    // La vraie valeur sera resynchronisée via l'événement backend
  } catch (error) {
    logger.error('Error in togglePlayPause', { error }, 'AudioPlayer');
  }
}

const rewind = () => {
  // Not supported in monitor mode
}

const skip = () => {
  // Not supported in monitor mode
}

const previous = async () => {
  logger.debug('Previous track requested', { currentPlaylist: currentPlaylist.value?.id, currentTrack: currentTrack.value?.filename }, 'AudioPlayer');
  // Suppression de tout verrouillage : on envoie la commande à chaque clic
  try {
    await apiService.controlPlaylist('previous');
  } catch (error) {
    logger.error('Error in previous', { error }, 'AudioPlayer');
  }
}

const next = async () => {
  logger.debug('Next track requested', { currentPlaylist: currentPlaylist.value?.id, currentTrack: currentTrack.value?.filename }, 'AudioPlayer');
  // Suppression de tout verrouillage : on envoie la commande à chaque clic
  try {
    await apiService.controlPlaylist('next');
  } catch (error) {
    logger.error('Error in next', { error }, 'AudioPlayer');
  }
}
</script>
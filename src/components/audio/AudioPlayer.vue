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
<template>
  <div class="flex items-center justify-center">
    <div class="w-2/3">
      <div class="bg-white border-slate-100 dark:bg-slate-800 dark:border-slate-500 border-b rounded-t-xl p-4 pb-6 sm:p-10 sm:pb-8 lg:p-6 xl:p-10 xl:pb-8 space-y-6 sm:space-y-8 lg:space-y-6 xl:space-y-8 items-center">
        <TrackInfo :track="currentTrack || undefined" />
        <ProgressBar
          :currentTime="currentTime"
          :duration="duration"
          @seek="handleSeek"
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

    <!-- Hidden audio element -->
    <audio
      ref="audioPlayer"
      :src="audioUrl"
      @ended="handleTrackEnd"
      @timeupdate="handleTimeUpdate"
      @loadedmetadata="handleMetadataLoaded"
      @error="handleAudioError"
    ></audio>
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
import { ref, watch, onUnmounted } from 'vue'
import TrackInfo from './TrackInfo.vue'
import ProgressBar from './ProgressBar.vue'
import PlaybackControls from './PlaybackControls.vue'
import type { Track, PlayList } from '../files/types'
import dataService from '@/services/dataService'
// We'll use $t in the template later, so keep it imported
import { i18n } from '@/i18n'

const { t: $t } = i18n

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
const audioPlayer = ref<HTMLAudioElement | null>(null)
const audioUrl = ref('')

// Watch for changes to the selected track
watch(() => props.selectedTrack, async (newTrack) => {
  if (newTrack) {
    currentTrack.value = newTrack
    audioUrl.value = dataService.downloadFileUrl(newTrack.number)
    if (audioPlayer.value) {
      await audioPlayer.value.load()
      await audioPlayer.value.play()
      isPlaying.value = true
    }
  }
}, { immediate: true })

/**
 * Toggle play/pause state of the audio
 */
const togglePlayPause = async () => {
  if (!audioPlayer.value || !currentTrack.value) return

  try {
    if (isPlaying.value) {
      await audioPlayer.value.pause()
    } else {
      await audioPlayer.value.play()
    }
    isPlaying.value = !isPlaying.value
  } catch (error) {
    console.error('Error during playback:', error)
  }
}

/**
 * Handle time update event from audio element
 */
const handleTimeUpdate = () => {
  if (audioPlayer.value) {
    currentTime.value = audioPlayer.value.currentTime
  }
}

/**
 * Handle metadata loaded event from audio element
 */
const handleMetadataLoaded = () => {
  if (audioPlayer.value) {
    duration.value = audioPlayer.value.duration
  }
}

/**
 * Seek to a specific time in the audio
 * @param {number} time - Target time in seconds
 */
const handleSeek = (time: number) => {
  if (audioPlayer.value) {
    audioPlayer.value.currentTime = time
    currentTime.value = time
  }
}

/**
 * Handle track end event
 */
const handleTrackEnd = () => {
  isPlaying.value = false
  currentTime.value = 0
  next()
}

/**
 * Handle audio error event
 */
const handleAudioError = (error: Event) => {
  console.error('Audio playback error:', error)
  isPlaying.value = false
}

/**
 * Rewind 10 seconds
 */
const rewind = () => {
  handleSeek(Math.max(0, currentTime.value - 10))
}

/**
 * Skip forward 10 seconds
 */
const skip = () => {
  handleSeek(Math.min(duration.value, currentTime.value + 10))
}

/**
 * Find the next or previous track in the playlist
 * @param {string} direction - Direction to find (next or previous)
 */
const findAdjacentTrack = (direction: 'next' | 'previous'): Track | null => {
  if (!props.playlist || !currentTrack.value) return null

  const currentIndex = props.playlist.tracks.findIndex(t => t.number === currentTrack.value?.number)
  if (currentIndex === -1) return null

  const targetIndex = direction === 'next' ? currentIndex + 1 : currentIndex - 1
  return props.playlist.tracks[targetIndex] || null
}

/**
 * Go to previous track
 */
const previous = () => {
  const prevTrack = findAdjacentTrack('previous')
  if (prevTrack) {
    currentTrack.value = prevTrack
    audioUrl.value = dataService.downloadFileUrl(prevTrack.number)
  }
}

/**
 * Go to next track
 */
const next = () => {
  const nextTrack = findAdjacentTrack('next')
  if (nextTrack) {
    currentTrack.value = nextTrack
    audioUrl.value = dataService.downloadFileUrl(nextTrack.number)
  }
}

// Cleanup on component unmount
onUnmounted(() => {
  if (audioPlayer.value) {
    audioPlayer.value.pause()
    audioPlayer.value.src = ''
  }
})
</script>
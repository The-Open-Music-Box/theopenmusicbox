<template>
  <div class="flex items-center justify-center">
    <div class="w-2/3">
      <div class="bg-white border-slate-100 dark:bg-slate-800 dark:border-slate-500 border-b rounded-t-xl p-4 pb-6 sm:p-10 sm:pb-8 lg:p-6 xl:p-10 xl:pb-8 space-y-6 sm:space-y-8 lg:space-y-6 xl:space-y-8 items-center">
        <TrackInfo :track="currentTrack" />
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
import { ref, onMounted, onUnmounted } from 'vue'
import TrackInfo from './TrackInfo.vue'
import ProgressBar from './ProgressBar.vue'
import PlaybackControls from './PlaybackControls.vue'

// State
const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(180)
const currentTrack = ref({
  name: 'New Album The Lorem', // Added name property
  trackNumber: '05',
  title: 'New Album The Lorem',
  artist: 'Spotisimo',
  imageUrl: null
})

let interval: number | null = null

// Methods
const updateProgress = () => {
  if (isPlaying.value) {
    currentTime.value = Math.min(currentTime.value + 0.1, duration.value)
    if (currentTime.value >= duration.value) {
      isPlaying.value = false
      if (interval) clearInterval(interval)
    }
  }
}

const togglePlayPause = () => {
  if (isPlaying.value) {
    if (interval) clearInterval(interval)
  } else {
    interval = setInterval(updateProgress, 100)
  }
  isPlaying.value = !isPlaying.value
}

const rewind = () => {
  currentTime.value = Math.max(0, currentTime.value - 10)
}

const skip = () => {
  currentTime.value = Math.min(duration.value, currentTime.value + 10)
}

const previous = () => {
  // Implement previous track logic
}

const next = () => {
  // Implement next track logic
}

// Lifecycle
onMounted(() => {
  if (isPlaying.value) {
    interval = setInterval(updateProgress, 100)
  }
})

onUnmounted(() => {
  if (interval) {
    clearInterval(interval)
  }
})
</script>
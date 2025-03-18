<template>
  <div class="flex flex-col items-center space-y-2">
    <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
      {{ track?.title || 'Aucun morceau sélectionné' }}
    </h2>
    <p class="text-sm text-gray-500 dark:text-gray-400">
      {{ track?.filename || '' }}
    </p>
    <div class="flex items-center space-x-4 text-sm text-gray-500 dark:text-gray-400">
      <span>Durée: {{ track ? formatDuration(track.duration) : '00:00' }}</span>
      <span>Lectures: {{ track?.play_counter || 0 }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps } from 'vue'
import type { Track } from '../files/types'

const props = defineProps<{
  track: Track | null | undefined
}>()

function formatDuration(duration: string): string {
  const seconds = parseInt(duration)
  if (isNaN(seconds)) return '00:00'
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`
}
</script>

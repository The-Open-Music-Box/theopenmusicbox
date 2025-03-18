<template>
  <div class="flex flex-col items-center space-y-2">
    <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
      {{ track?.title || $t('audio.noTrackSelected') }}
    </h2>
    <p class="text-sm text-gray-500 dark:text-gray-400">
      {{ track?.filename || '' }}
    </p>
    <div class="flex items-center space-x-4 text-sm text-gray-500 dark:text-gray-400">
      <span>{{ $t('audio.duration') }}: {{ track ? formatDuration(track.duration) : '00:00' }}</span>
      <span>{{ $t('audio.plays') }}: {{ track?.play_counter || 0 }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * TrackInfo Component
 *
 * Displays metadata about the currently selected track.
 * Shows title, filename, duration, and play count.
 */

import type { Track } from '../files/types'
import { i18n } from '@/i18n'

const { t: $t } = i18n

defineProps<{
  /** The track to display information for */
  track: Track | null | undefined
}>()

/**
 * Format duration in seconds to MM:SS format
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

<template>
  <div class="flex flex-col items-center space-y-2">
    <h2 :class="['text-xl font-semibold', colors.text.primary]">
      {{ track?.title || t('audio.noTrackSelected') }}
    </h2>
    <!-- Nom de fichier masqué -->
    <div :class="['flex items-center space-x-4 text-sm', colors.text.secondary]">
      <span>{{ t('audio.duration') }}: {{ track ? formatDuration(track.duration) : '00:00' }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { colors } from '@/theme/colors'
/**
 * TrackInfo Component
 *
 * Displays metadata about the currently selected track.
 * Shows title, filename, duration, and play count.
 */

import type { Track } from '../files/types'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

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

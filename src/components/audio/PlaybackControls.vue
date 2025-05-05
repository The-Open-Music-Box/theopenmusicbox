<template>
  <div class="flex items-center justify-between w-full max-w-full gap-x-0 sm:gap-x-10 px-4 sm:px-6">
    <!-- Groupe gauche -->
    <div class="flex items-center gap-x-0 sm:gap-x-6">
      <button
        type="button"
        class="block"
        :aria-label="$t('player.previous')"
        @click="handlePrevious()"
      >
        <svg width="24" height="24" fill="none">
          <path
            d="m10 12 8-6v12l-8-6Z"
            fill="currentColor"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
          <path
            d="M6 6v12"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
      </button>
      <button
        type="button"
        :aria-label="$t('player.rewind')"
        @click="$emit('rewind')"
      >
        <svg width="24" height="24" fill="none">
          <path
            d="M6.492 16.95c2.861 2.733 7.5 2.733 10.362 0 2.861-2.734 2.861-7.166 0-9.9-2.862-2.733-7.501-2.733-10.362 0A7.096 7.096 0 0 0 5.5 8.226"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
          <path
            d="M5 5v3.111c0 .491.398.889.889.889H9"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
      </button>
    </div>
    <!-- Bouton central -->
    <button
      type="button"
      class="bg-white text-slate-900 dark:bg-slate-100 dark:text-slate-700 -my-2 mx-auto w-16 h-16 sm:w-20 sm:h-20 rounded-full ring-1 ring-slate-900/5 shadow-md flex items-center justify-center"
      :aria-label="$t('player.playPause')"
      @click="$emit('togglePlayPause')"
    >
      <svg v-if="isPlaying" width="30" height="32" fill="currentColor">
        <rect x="6" y="4" width="4" height="24" rx="2" />
        <rect x="20" y="4" width="4" height="24" rx="2" />
      </svg>
      <svg v-else width="30" height="32" fill="currentColor">
        <polygon points="5,3 25,16 5,29" />
      </svg>
    </button>
    <!-- Groupe droit -->
    <div class="flex items-center gap-x-0 sm:gap-x-6">
      <button
        type="button"
        :aria-label="$t('player.skip')"
        @click="$emit('skip')"
      >
        <svg width="24" height="24" fill="none">
          <path
            d="M17.509 16.95c-2.862 2.733-7.501 2.733-10.363 0-2.861-2.734-2.861-7.166 0-9.9 2.862-2.733 7.501-2.733 10.363 0 .38.365.711.759.991 1.176"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
          <path
            d="M19 5v3.111c0 .491-.398.889-.889.889H15"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
      </button>
      <button
        type="button"
        class="block"
        :aria-label="$t('player.next')"
        @click="handleNext()"
      >
        <svg width="24" height="24" fill="none">
          <path
            d="M14 12 6 6v12l8-6Z"
            fill="currentColor"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
          <path
            d="M18 6v12"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * PlaybackControls Component
 *
 * Provides a set of controls for audio playback including:
 * - Play/pause button
 * - Previous/next track buttons
 * - Rewind/skip buttons
 */

import { i18n } from '@/i18n'

const { t: $t } = i18n

defineProps<{
  /** Whether audio is currently playing */
  isPlaying: boolean
}>()

const emit = defineEmits<{
  /** Emitted when play/pause button is clicked */
  (e: 'togglePlayPause'): void;
  /** Emitted when previous track button is clicked */
  (e: 'previous'): void;
  /** Emitted when next track button is clicked */
  (e: 'next'): void;
  /** Emitted when rewind button is clicked */
  (e: 'rewind'): void;
  /** Emitted when skip button is clicked */
  (e: 'skip'): void;
}>()

const handlePrevious = () => {
  console.log('[PlaybackControls] Previous button clicked')
  emit('previous')
}

const handleNext = () => {
  console.log('[PlaybackControls] Next button clicked')
  emit('next')
}
</script>

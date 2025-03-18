<template>
    <div class="flex items-center space-x-4">
      <img
      src="@/assets/placeholder.jpg"
      :alt="track.title"
        width="88"
        height="88"
        class="flex-none rounded-lg bg-slate-100"
        loading="lazy"
      />
      <div class="min-w-0 flex-auto space-y-1 font-semibold">
        <p class="text-cyan-500 dark:text-cyan-400 text-sm leading-6">
          <abbr title="Track">Piste:</abbr> {{ track.number }}
        </p>
        <h2 class="text-slate-500 dark:text-slate-400 text-sm leading-6 truncate">
          {{ track.title }}
        </h2>
        <p class="text-slate-900 dark:text-slate-50 text-lg">{{ formatDuration(track.duration) }}</p>
      </div>
    </div>
  </template>
  
  <script setup lang="ts">
  import { defineProps } from 'vue'
  import type { Track } from '../files/types'

  defineProps<{
    track: Track
  }>()

  function formatDuration(duration: string): string {
    const seconds = parseInt(duration)
    if (isNaN(seconds)) return '00:00'
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`
  }
  </script>
  
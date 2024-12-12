<template>
    <div class="flex items-center space-x-4">
      <img
      src="@/assets/placeholder.jpg"
      :alt="track.name"
        width="88"
        height="88"
        class="flex-none rounded-lg bg-slate-100"
        loading="lazy"
      />
      <div class="min-w-0 flex-auto space-y-1 font-semibold">
        <p class="text-cyan-500 dark:text-cyan-400 text-sm leading-6">
          <abbr title="Track">Track:</abbr> {{ track.trackNumber }}
        </p>
        <h2 class="text-slate-500 dark:text-slate-400 text-sm leading-6 truncate">
          {{ track.title }}
        </h2>
        <p class="text-slate-900 dark:text-slate-50 text-lg">{{ track.artist }}</p>
      </div>
    </div>
  </template>
  
  <script setup lang="ts">
  import { defineProps } from 'vue'

  interface Track {
  imageUrl?: string | null // Updated to allow null
  name: string
  trackNumber: string | number
  title: string
  artist: string
}

  
  defineProps<{
    track: Track
  }>()
  </script>
  
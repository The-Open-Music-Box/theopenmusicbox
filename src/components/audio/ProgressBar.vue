<template>
  <div class="space-y-2">
    <div class="relative">
      <div class="bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
        <div
          class="bg-cyan-500 dark:bg-cyan-400 h-2"
          :style="{ width: `${progressPercentage}%` }"
          role="progressbar"
          aria-label="music progress"
          :aria-valuenow="currentTime"
          :aria-valuemin="0"
          :aria-valuemax="duration"
        ></div>
      </div>
      <div
        class="absolute top-1/2 transform -translate-y-1/2"
        :style="{ left: `${progressPercentage}%` }"
      >
        <div class="w-4 h-4 flex items-center justify-center bg-white rounded-full shadow">
          <div class="w-1.5 h-1.5 bg-cyan-500 dark:bg-cyan-400 rounded-full ring-1 ring-inset ring-slate-900/5"></div>
        </div>
      </div>
    </div>
    <div class="flex justify-between text-sm leading-6 font-medium tabular-nums">
      <div class="text-cyan-500 dark:text-slate-100">{{ formatTime(currentTime) }}</div>
      <div class="text-slate-500 dark:text-slate-400">{{ formatTime(duration) }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps, computed } from 'vue'
const props = defineProps<{
  currentTime: number
  duration: number
}>()

const progressPercentage = computed(() => (props.currentTime / props.duration) * 100)

const formatTime = (time: number) => {
  const minutes = Math.floor(time / 60)
  const seconds = Math.floor(time % 60).toString().padStart(2, '0')
  return `${minutes}:${seconds}`
}
</script>
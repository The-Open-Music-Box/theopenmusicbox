<template>
  <div class="flex justify-end">
    <button
      type="submit"
      :disabled="loading"
      class="rounded-md bg-indigo-600 px-3.5 py-2.5 text-center text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed"
    >
      <span v-if="loading">Sending...</span>
      <span v-else>Send message</span>
    </button>
  </div>
</template>

<script setup lang="ts">
import { defineProps } from 'vue'

defineProps<{
  loading: boolean
}>()
</script>
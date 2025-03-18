<template>
  <div v-if="errors.length" class="mt-4">
    <p v-for="(error, index) in errors"
       :key="index"
       class="text-sm text-red-600">
      {{ error }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { defineProps } from 'vue'

defineProps<{
  errors: string[]
}>()
</script>
<template>
  <div v-if="errors.length" class="mt-4">
    <p v-for="(error, index) in errors"
       :key="index"
       :class="[colors.error.main, 'text-sm']">
      {{ error }}
    </p>
  </div>
</template>

<script setup lang="ts">
/**
 * FileValidationMessages Component
 *
 * Displays validation error messages for file uploads.
 * Shows error messages in a consistent format with appropriate styling.
 */

import { colors } from '@/theme/colors'

defineProps<{
  /** Array of error message strings to display */
  errors: string[]
}>()
</script>
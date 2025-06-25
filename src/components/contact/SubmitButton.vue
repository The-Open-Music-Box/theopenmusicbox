<template>
  <div class="flex justify-end">
    <button
      type="submit"
      :disabled="loading"
      :class="[
        'bg-primary',
        'rounded-md px-3.5 py-2.5 text-center text-sm font-semibold text-onPrimary shadow-sm',
        'hover:bg-primary-light',
        'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2',
        'focus-visible:outline-focus',
        'disabled:opacity-50 disabled:cursor-not-allowed'
      ]"
    >
      <span v-if="loading">{{ t('contact.sending') }}</span>
      <span v-else>{{ t('contact.sendMessage') }}</span>
    </button>
  </div>
</template>

<script setup lang="ts">
/**
 * SubmitButton Component
 *
 * A styled submit button for forms with loading state indication.
 * Shows different text depending on loading state.
 */

import { useI18n } from 'vue-i18n'
import { colors } from '@theme/colors'

const { t } = useI18n()

defineProps<{
  /** Whether the form is currently submitting */
  loading: boolean
}>()
</script>
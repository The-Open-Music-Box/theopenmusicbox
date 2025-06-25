<template>
  <dl class="mt-10 space-y-4 text-base leading-7 text-onBackground">
    <div v-for="detail in details" :key="detail.type" class="flex gap-x-4">
      <dt class="flex-none">
        <span class="sr-only">{{ detail.type }}</span>
        <component
          :is="detail.icon"
          class="h-7 w-6 text-disabled"
          aria-hidden="true"
        />
      </dt>
      <dd>
        <template v-if="detail.href">
          <a
            :href="detail.href"
            class="hover:text-primary"
          >{{ detail.content }}</a>
        </template>
        <template v-else>
          {{ detail.content }}
        </template>
      </dd>
    </div>
  </dl>
</template>

<script setup lang="ts">
/**
 * ContactDetails Component
 *
 * Displays a list of contact details with appropriate icons.
 * Supports clickable links for email, phone, etc.
 */

import { useI18n } from 'vue-i18n'

const { t } = useI18n()

interface ContactDetail {
  /** Type of contact detail (address, phone, email) */
  type: string;
  /** Icon component name to render */
  icon: string;
  /** Content text to display */
  content: string;
  /** Optional href for clickable items */
  href?: string;
}

defineProps<{
  /** Array of contact details to display */
  details: ContactDetail[];
}>()
</script>

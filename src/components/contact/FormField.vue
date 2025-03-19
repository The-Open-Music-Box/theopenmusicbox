<template>
  <div :class="[field.colSpan === 2 ? 'sm:col-span-2' : '']">
    <label :for="field.id" :class="[colors.text.primary, 'block text-sm font-semibold leading-6']">
      {{ $t(`contact.${field.id}`) }}
    </label>
    <div class="mt-2.5">
      <textarea
        v-if="field.type === 'textarea'"
        :id="field.id"
        :name="field.id"
        :rows="field.rows"
        :value="value"
        @input="handleInput"
        class="block w-full rounded-md border-0 px-3.5 py-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
      />
      <input
        v-else
        :id="field.id"
        :name="field.id"
        :type="field.type"
        :autocomplete="field.autocomplete"
        :value="value"
        @input="handleInput"
        class="block w-full rounded-md border-0 px-3.5 py-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * FormField Component
 *
 * A reusable form field component that supports both input and textarea types.
 * Handles user input events and applies consistent styling.
 */

import { i18n } from '@/i18n'
import { colors } from '@theme/colors'

const { t: $t } = i18n

interface Field {
  /** Unique identifier for the field */
  id: string;
  /** Label text for the field */
  label: string;
  /** Input type (text, email, textarea, etc.) */
  type: string;
  /** HTML autocomplete attribute */
  autocomplete?: string;
  /** Number of rows for textarea */
  rows?: number;
  /** Column span in grid layout */
  colSpan: number;
}

const props = defineProps<{
  /** Field configuration */
  field: Field;
  /** Current field value */
  value: string;
}>()

const emit = defineEmits<{
  /** Emitted when input value changes */
  (e: 'input', value: string): void;
  /** Emitted with field ID and new value */
  (e: 'update', fieldId: string, value: string): void;
}>()

/**
 * Handle input event from form control
 * @param {Event} event - Input event object
 */
const handleInput = (event: Event) => {
  const target = event.target as HTMLInputElement | HTMLTextAreaElement
  emit('input', target.value)
  emit('update', props.field.id, target.value)
}
</script>
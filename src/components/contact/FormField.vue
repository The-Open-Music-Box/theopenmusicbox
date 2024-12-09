// components/contact/FormField.vue
<template>
  <div :class="[field.colSpan === 2 ? 'sm:col-span-2' : '']">
    <label :for="field.id" class="block text-sm font-semibold leading-6 text-gray-900">
      {{ field.label }}
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
import { defineProps, defineEmits } from 'vue'

interface Field {
  id: string
  label: string
  type: string
  autocomplete?: string
  rows?: number
  colSpan: number
}

const props = defineProps<{
  field: Field
  value: string
}>()

const emit = defineEmits<{
  (e: 'input', value: string): void
  (e: 'update', fieldId: string, value: string): void
}>()

const handleInput = (event: Event) => {
  const target = event.target as HTMLInputElement | HTMLTextAreaElement
  emit('input', target.value)
  emit('update', props.field.id, target.value)
}
</script>
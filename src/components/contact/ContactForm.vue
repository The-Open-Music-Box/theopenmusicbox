<template>
  <form @submit.prevent="handleSubmit" class="mx-auto max-w-xl lg:mr-0 lg:max-w-lg">
    <div class="grid grid-cols-1 gap-x-8 gap-y-6 sm:grid-cols-2">
      <FormField
        v-for="field in formFields"
        :key="field.id"
        :field="field"
        :value="formData[field.id]"
        @update="updateField"
      />
    </div>
    <SubmitButton class="mt-8" :loading="isSubmitting" />
  </form>
</template>

<script setup lang="ts">
/**
 * ContactForm Component
 *
 * A form for users to send contact messages.
 * Manages form data, validation, and submission.
 */
import { ref, reactive } from 'vue'
import FormField from './FormField.vue'
import SubmitButton from './SubmitButton.vue'
import { i18n } from '@/i18n'

const { t: $t } = i18n

interface ContactFormInput {
  id: string;  // Changed from keyof FormData to string
  label: string;
  type: string;
  autocomplete?: string;
  rows?: number;
  colSpan: number;
}

interface FormData {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  message: string;
  [key: string]: string; // Index signature for dynamic access
}

/**
 * Form field definitions
 */
const formFields: ContactFormInput[] = [
  {
    id: 'firstName',
    label: 'First name',
    type: 'text',
    autocomplete: 'given-name',
    colSpan: 1
  },
  {
    id: 'lastName',
    label: 'Last name',
    type: 'text',
    autocomplete: 'family-name',
    colSpan: 1
  },
  {
    id: 'email',
    label: 'Email',
    type: 'email',
    autocomplete: 'email',
    colSpan: 2
  },
  {
    id: 'phone',
    label: 'Phone number',
    type: 'tel',
    autocomplete: 'tel',
    colSpan: 2
  },
  {
    id: 'message',
    label: 'Message',
    type: 'textarea',
    rows: 4,
    colSpan: 2
  }
]

/**
 * Form data object with initial empty values
 */
const formData = reactive<FormData>({
  firstName: '',
  lastName: '',
  email: '',
  phone: '',
  message: ''
})

/** Form submission state */
const isSubmitting = ref(false)

/**
 * Update a field value in the form data
 * @param {string} fieldId - Field identifier
 * @param {string} value - New field value
 */
const updateField = (fieldId: string, value: string) => {
  formData[fieldId as keyof FormData] = value
}

/**
 * Handle form submission
 */
const handleSubmit = async () => {
  try {
    isSubmitting.value = true
    // Implement form submission logic here
    await new Promise(resolve => setTimeout(resolve, 1000))
    console.log('Form submitted:', formData)
    // Reset form after successful submission
    Object.keys(formData).forEach(key => {
      formData[key] = '';
    });
  } catch (error) {
    console.error('Error submitting form:', error)
  } finally {
    isSubmitting.value = false
  }
}
</script>
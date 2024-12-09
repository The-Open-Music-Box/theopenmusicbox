// components/contact/ContactForm.vue
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
  import { ref, reactive } from 'vue'
  import FormField from './FormField.vue'
  import SubmitButton from './SubmitButton.vue'
  
  interface ContactFormInput {
  id: keyof FormData
  label: string
  type: string
  autocomplete?: string
  rows?: number
  colSpan: number
}

interface FormData {
  firstName: string
  lastName: string
  email: string
  phone: string
  message: string
  [key: string]: string // Index signature pour permettre l'accès dynamique
}

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
  
  const formData = reactive<FormData>({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    message: ''
  })
  
  const isSubmitting = ref(false)

  const updateField = (fieldId: keyof FormData, value: string) => {
    formData[fieldId] = value
  }
  
  const handleSubmit = async () => {
    try {
      isSubmitting.value = true
      // Implement form submission logic here
      await new Promise(resolve => setTimeout(resolve, 1000))
      console.log('Form submitted:', formData)
    } catch (error) {
      console.error('Error submitting form:', error)
    } finally {
      isSubmitting.value = false
    }
  }
  </script>
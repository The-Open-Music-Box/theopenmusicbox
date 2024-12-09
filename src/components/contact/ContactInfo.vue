// components/contact/ContactInfo.vue
<template>
  <div class="mx-auto max-w-xl lg:mx-0 lg:max-w-lg">
    <BackgroundDecoration />
    <h2 class="text-3xl font-bold tracking-tight text-gray-900">
      Get in touch
    </h2>
    <p class="mt-6 text-lg leading-8 text-gray-600">
      {{ description }}
    </p>
    <ContactDetails :details="contactDetails" />
  </div>
</template>

<script setup lang="ts">
import BackgroundDecoration from './BackgroundDecoration.vue'
import ContactDetails from './ContactDetails.vue'

const description = 'Proin volutpat consequat porttitor cras nullam gravida at. Orci molestie a eu arcu. Sed ut tincidunt integer elementum id sem. Arcu sed malesuada et magna.'

const contactDetails = [
  {
    type: 'address',
    icon: 'BuildingOffice2Icon',
    content: '545 Mavis Island\nChicago, IL 99191'
  },
  {
    type: 'phone',
    icon: 'PhoneIcon',
    content: '+1 (555) 234-5678',
    href: 'tel:+1 (555) 234-5678'
  },
  {
    type: 'email',
    icon: 'EnvelopeIcon',
    content: 'hello@example.com',
    href: 'mailto:hello@example.com'
  }
]
</script>

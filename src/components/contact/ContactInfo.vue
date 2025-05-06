<template>
  <div class="flex justify-center items-center min-h-[60vh] py-8">
  <div class="w-full max-w-md bg-white border border-gray-200 rounded-xl shadow-lg p-8 relative">
    <BackgroundDecoration class="absolute inset-0 pointer-events-none z-0" />
    
    <h2 :class="[colors.text.primary, 'text-3xl font-bold tracking-tight']">
      {{ t('contact.getInTouch') }}
    </h2>
    <p :class="[colors.text.secondary, 'mt-6 text-lg leading-8']">
      {{ description }}
    </p>
    <ContactDetails :details="contactDetails" />
  </div>
    </div>
</div>
</template>

<script setup lang="ts">
/**
 * ContactInfo Component
 *
 * Displays contact information and description.
 * Includes background decorations and detailed contact options.
 */
import BackgroundDecoration from './BackgroundDecoration.vue'
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
import ContactDetails from './ContactDetails.vue'
import { colors } from '@theme/colors'

/**
 * Descriptive text for contact section
 */
const description = 'Proin volutpat consequat porttitor cras nullam gravida at. Orci molestie a eu arcu. Sed ut tincidunt integer elementum id sem. Arcu sed malesuada et magna.'

/**
 * Contact details with icons and content
 */
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

// components/contact/ContactDetails.vue
<template>
  <dl class="mt-10 space-y-4 text-base leading-7 text-gray-600">
    <div v-for="detail in details" :key="detail.type" class="flex gap-x-4">
      <dt class="flex-none">
        <span class="sr-only">{{ detail.type }}</span>
        <component 
          :is="detail.icon" 
          class="h-7 w-6 text-gray-400" 
          aria-hidden="true" 
        />
      </dt>
      <dd>
        <template v-if="detail.href">
          <a 
            :href="detail.href" 
            class="hover:text-gray-900"
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
import { BuildingOffice2Icon, PhoneIcon, EnvelopeIcon } from '@heroicons/vue/24/outline'
import { defineProps } from 'vue'

interface ContactDetail {
  type: string
  icon: string
  content: string
  href?: string
}

defineProps<{
  details: ContactDetail[]
}>()
</script>

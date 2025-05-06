<template>
  <div class="flex justify-center items-center min-h-[70vh] bg-gray-50">
    <div class="w-full max-w-md bg-white border border-gray-200 rounded-xl shadow-lg p-8">
      <h2 class="text-3xl font-bold tracking-tight text-gray-900 mb-4">Get in touch</h2>
<p class="mb-4 text-base text-gray-700">{{ t('contact.welcomeMsg') }}</p>
      
      <dl class="space-y-4 text-base leading-7 text-gray-600">
        <!-- Email -->
        <div class="flex gap-x-4 items-center">
          <dt class="flex-none">
            <EnvelopeIcon class="h-7 w-6 text-gray-400" aria-hidden="true" />
          </dt>
          <dd>
            <a class="font-semibold text-indigo-600 hover:underline" href="mailto:hi@theopenmusicbox.com">{{ t('contact.emailValue') }}</a>
          </dd>
        </div>
        <!-- Website -->
        <div class="flex gap-x-4 items-center">
          <dt class="flex-none">
            <GlobeAltIcon class="h-7 w-6 text-gray-400" aria-hidden="true" />
          </dt>
          <dd>
            <a class="font-semibold text-indigo-600 hover:underline" href="https://theopenmusicbox.com" target="_blank" rel="noopener">{{ t('contact.website') }}</a>
          </dd>
        </div>
        <!-- Bluesky -->
        <div class="flex gap-x-4 items-center">
          <dt class="flex-none">
            <HashtagIcon class="h-7 w-6 text-gray-400" aria-hidden="true" />
          </dt>
          <dd>
            <a class="font-semibold text-indigo-600 hover:underline" href="https://bsky.app/profile/theopenmusicbox.com" target="_blank" rel="noopener">{{ t('contact.bsky') }}</a>
          </dd>
        </div>
        <!-- Facebook -->
        <div class="flex gap-x-4 items-center">
          <dt class="flex-none">
            <!-- Facebook SVG icon -->
            <span class="inline-block h-7 w-6 text-gray-400" aria-hidden="true">
              <svg fill="currentColor" viewBox="0 0 24 24" class="h-7 w-6"><path d="M22.675 0h-21.35C.597 0 0 .6 0 1.326v21.348C0 23.4.597 24 1.326 24h11.495v-9.294H9.692v-3.622h3.129V8.413c0-3.1 1.893-4.788 4.659-4.788 1.325 0 2.463.099 2.797.143v3.24l-1.918.001c-1.504 0-1.797.715-1.797 1.763v2.313h3.587l-.467 3.622h-3.12V24h6.116C23.403 24 24 23.4 24 22.674V1.326C24 .6 23.403 0 22.675 0"/></svg>
            </span>
          </dt>
          <dd>
            <a class="font-semibold text-indigo-600 hover:underline" href="https://facebook.com/theopenmusicbox" target="_blank" rel="noopener">{{ t('contact.facebook') }}</a>
          </dd>
        </div>
        <!-- GitHub -->
        <div class="flex gap-x-4 items-center">
          <dt class="flex-none">
            <CodeBracketIcon class="h-7 w-6 text-gray-400" aria-hidden="true" />
          </dt>
          <dd>
            <a class="font-semibold text-indigo-600 hover:underline" href="https://github.com/The-Open-Music-Box/firmware" target="_blank" rel="noopener">{{ t('contact.github') }}</a>
          </dd>
        </div>
        <!-- Ajoutez d'autres contacts ici -->
      </dl>
    </div>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import {
  EnvelopeIcon,
  GlobeAltIcon,
  HashtagIcon,
  CodeBracketIcon,
} from '@heroicons/vue/24/outline'
// FacebookIcon is not in Heroicons; use SVG inline below
const { t } = useI18n()
</script>

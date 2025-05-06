<template>
  <div class="contact">
    <div class="relative isolate bg-white">
      <div class="mx-auto grid max-w-7xl grid-cols-1 lg:grid-cols-2">
        <div class="relative px-6 pb-20 pt-24 sm:pt-32 lg:static lg:px-8 lg:py-48">
          <div class="mx-auto max-w-xl lg:mx-0 lg:max-w-lg">
            <div
              class="absolute inset-y-0 left-0 -z-10 w-full overflow-hidden bg-gray-100 ring-1 ring-gray-900/10 lg:w-1/2">
              <svg
                class="absolute inset-0 h-full w-full stroke-gray-200 [mask-image:radial-gradient(100%_100%_at_top_right,white,transparent)]"
                aria-hidden="true">
                <defs>
                  <pattern id="83fd4e5a-9d52-42fc-97b6-718e5d7ee527" width="200" height="200" x="100%" y="-1"
                    patternUnits="userSpaceOnUse">
                    <path d="M130 200V.5M.5 .5H200" fill="none" />
                  </pattern>
                </defs>
                <rect width="100%" height="100%" stroke-width="0" fill="white" />
                <svg x="100%" y="-1" class="overflow-visible fill-gray-50">
                  <path d="M-470.5 0h201v201h-201Z" stroke-width="0" />
                </svg>
                <rect width="100%" height="100%" stroke-width="0" fill="url(#83fd4e5a-9d52-42fc-97b6-718e5d7ee527)" />
              </svg>
            </div>
            <h2 class="text-3xl font-bold tracking-tight text-gray-900">
              Get in touch
            </h2>
            <p class="mt-6 text-lg leading-8 text-gray-600">
              Proin volutpat consequat porttitor cras nullam gravida at. Orci
              molestie a eu arcu. Sed ut tincidunt integer elementum id sem.
              Arcu sed malesuada et magna.
            </p>
            <dl class="mt-10 space-y-4 text-base leading-7 text-gray-600">
              <!-- Email -->
              <div class="flex gap-x-4 items-center">
                <dt class="flex-none">
                  <EnvelopeIcon class="h-7 w-6 text-gray-400" aria-hidden="true" />
                </dt>
                <dd>
                  <span class="font-semibold">{{ t('contact.emailValue') }}</span>
                  <a class="ml-2 text-indigo-600 hover:underline" href="mailto:hi@theopenmusicbox.com">hi@theopenmusicbox.com</a>
                </dd>
              </div>
              <!-- Website -->
              <div class="flex gap-x-4 items-center">
                <dt class="flex-none">
                  <GlobeAltIcon class="h-7 w-6 text-gray-400" aria-hidden="true" />
                </dt>
                <dd>
                  <span class="font-semibold">{{ t('contact.website') }}</span>
                  <a class="ml-2 text-indigo-600 hover:underline" href="https://theopenmusicbox.com" target="_blank" rel="noopener">theopenmusicbox.com</a>
                </dd>
              </div>
              <!-- Bluesky -->
              <div class="flex gap-x-4 items-center">
                <dt class="flex-none">
                  <HashtagIcon class="h-7 w-6 text-gray-400" aria-hidden="true" />
                </dt>
                <dd>
                  <span class="font-semibold">{{ t('contact.bsky') }}</span>
                  <a class="ml-2 text-indigo-600 hover:underline" href="https://bsky.app/profile/theopenmusicbox.com" target="_blank" rel="noopener">bsky.app/profile/theopenmusicbox.com</a>
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
                  <span class="font-semibold">{{ t('contact.facebook') }}</span>
                  <a class="ml-2 text-indigo-600 hover:underline" href="https://facebook.com/theopenmusicbox" target="_blank" rel="noopener">facebook.com/theopenmusicbox</a>
                </dd>
              </div>
              <!-- GitHub -->
              <div class="flex gap-x-4 items-center">
                <dt class="flex-none">
                  <CodeBracketIcon class="h-7 w-6 text-gray-400" aria-hidden="true" />
                </dt>
                <dd>
                  <span class="font-semibold">{{ t('contact.github') }}</span>
                  <a class="ml-2 text-indigo-600 hover:underline" href="https://github.com/The-Open-Music-Box/firmware" target="_blank" rel="noopener">github.com/The-Open-Music-Box/firmware</a>
                </dd>
              </div>
            </dl>
          </div>
        </div>

      </div>
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

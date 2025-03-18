<template>
  <div class="absolute inset-0 -z-10 overflow-hidden">
    <svg
      class="absolute left-0 top-0 h-full w-full [mask-image:radial-gradient(100%_100%_at_top_left,white,transparent)]"
      aria-hidden="true"
    >
      <defs>
        <pattern
          id="83fd4e5a-9d52-42fc-97b6-718e5d7ee527"
          width="200"
          height="200"
          x="50%"
          y="-1"
          patternUnits="userSpaceOnUse"
        >
          <path d="M100 200V.5M.5 .5H200" fill="none" :stroke="colors.border.light" />
        </pattern>
      </defs>
      <svg x="50%" y="-1" class="overflow-visible fill-gray-50 dark:fill-gray-900">
        <path
          d="M-100.5 0h201v201h-201Z M699.5 0h201v201h-201Z M499.5 400h201v201h-201Z M-300.5 600h201v201h-201Z"
          stroke-width="0"
        />
      </svg>
      <rect width="100%" height="100%" stroke-width="0" :fill="'url(#83fd4e5a-9d52-42fc-97b6-718e5d7ee527)'" />
    </svg>
  </div>
</template>

<script setup lang="ts">
/**
 * BackgroundDecoration Component
 *
 * Provides a subtle grid pattern background decoration for sections.
 * Uses SVG patterns for a consistent visual texture.
 */
 import { colors } from '@theme/colors';
</script>

<template>
  <div class="settings-page max-w-2xl mx-auto py-10 px-4">
    <h1 class="text-2xl font-bold mb-6">{{ t('settings.title') }}</h1>
    <div class="space-y-6">
      <section>
        <h2 class="text-lg font-semibold mb-2">{{ t('settings.language') }}</h2>
        <select v-model="selectedLocale" @change="changeLocale" class="border rounded px-2 py-1">
          <option v-for="locale in availableLocales" :key="locale" :value="locale">
            {{ t('settings.locales.' + locale) }}
          </option>
        </select>
      </section>
      <section>
        <h2 class="text-lg font-semibold mb-2">{{ t('settings.systemStatus') }}</h2>
        <StatsInfo />
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import StatsInfo from '../components/StatsInfo.vue'

const { t, locale, availableLocales } = useI18n()
const selectedLocale = ref(locale.value)

function changeLocale() {
  locale.value = selectedLocale.value
}
</script>

<style scoped>
.settings-page {
  background: var(--color-surface);
  border-radius: 1rem;
  box-shadow: 0 2px 8px var(--color-shadow);
}
</style>

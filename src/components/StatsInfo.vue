<template>
  <div class="bg-surface rounded-lg shadow p-6">
    <div v-if="systemHealth">
      <h3 class="text-base font-semibold leading-6 text-onBackground mb-4">Health Status (raw)</h3>
      <div class="space-y-2">
        <template v-for="(value, key) in systemHealth" :key="key">
          <div v-if="typeof value !== 'object' || value === null">
            <span class="font-medium text-onSurface">{{ key }}:</span>
            <span class="ml-2 text-onBackground">{{ value }}</span>
          </div>
          <div v-else>
            <span class="font-medium text-onSurface">{{ key }}:</span>
            <pre class="bg-background rounded p-2 mt-1 text-xs text-onBackground overflow-x-auto">{{ formatJson(value) }}</pre>
          </div>
        </template>
      </div>
    </div>
    <div v-else class="text-disabled">Loading health status...</div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import dataService from '../services/dataService'

const systemHealth = ref<any>(null)
const healthCheckInterval = ref<number | null>(null)

const checkHealth = async () => {
  try {
    const response = await dataService.checkHealth()
    systemHealth.value = response
  } catch (error) {
    systemHealth.value = { error: 'Failed to fetch health status' }
  }
}

function formatJson(obj: any) {
  return JSON.stringify(obj, null, 2)
}

onMounted(() => {
  checkHealth()
  healthCheckInterval.value = window.setInterval(checkHealth, 30000)
})

onUnmounted(() => {
  if (healthCheckInterval.value) {
    clearInterval(healthCheckInterval.value)
  }
})
</script>
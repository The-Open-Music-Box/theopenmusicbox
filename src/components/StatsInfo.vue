<template>
  <div class="space-y-6">
    <!-- General Information -->
    <div>
      <h3 class="text-base font-semibold leading-6 text-gray-900">
        {{ $t('stats.generalInfo') }}
      </h3>
      <dl class="mt-5 grid grid-cols-1 gap-5 sm:grid-cols-3">
        <div
          v-for="item in stats"
          :key="item.name"
          class="overflow-hidden rounded-lg bg-white px-4 py-5 shadow sm:p-6"
        >
          <dt class="truncate text-sm font-medium text-gray-500">
            {{ $t(`stats.${item.name}`) }}
          </dt>
          <dd class="mt-1 text-3xl font-semibold tracking-tight text-gray-900">
            {{ item.stat }}
          </dd>
        </div>
      </dl>
    </div>

    <!-- System Status -->
    <div>
      <div class="flex items-center justify-between">
        <h3 class="text-base font-semibold leading-6 text-gray-900">
          {{ $t('stats.systemStatus') }}
        </h3>
        <span
          :class="[
            'px-2 py-1 text-xs font-medium rounded-full',
            systemHealth?.status === 'healthy'
              ? getColor('bg', 'success.light') + ' ' + getColor('text', 'success.dark')
              : getColor('bg', 'error.light') + ' ' + getColor('text', 'error.dark')
          ]"
        >
          {{ systemHealth?.status || 'unknown' }}
        </span>
      </div>

      <!-- Components Grid -->
      <div v-if="hasComponents" class="mt-5 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
        <div
          v-for="(component, name) in systemHealth?.components"
          :key="name"
          class="flex flex-col rounded-lg bg-white shadow"
        >
          <div class="flex items-center justify-between p-4 border-b border-gray-200">
            <h4 class="text-sm font-medium text-gray-900 capitalize">
              {{ name }}
            </h4>
            <span
              :class="[
                'px-2 py-1 text-xs font-medium rounded-full',
                getStatusColor(component.status)
              ]"
            >
              {{ component.status }}
            </span>
          </div>
          <div class="p-4">
            <p class="text-xs text-gray-500">
              {{ $t('stats.lastUpdate') }}: {{ formatTimestamp(component.timestamp) }}
            </p>
          </div>
        </div>
      </div>
      <div v-else class="mt-5 text-center text-gray-500">
        {{ $t('stats.noComponents') }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * StatsInfo Component
 *
 * Displays system health and status information.
 * Shows general system stats and detailed component health.
 */
import { ref, computed, onMounted, onUnmounted } from 'vue'
import dataService from '../services/dataService'
import { i18n } from '@/i18n'
// Only import getColor if we actually use it in the template
import { colors } from '@theme/colors'

const { t: $t } = i18n

const stats = ref([
  { name: 'battery', stat: '71%' },
  { name: 'trackCount', stat: '12' },
  { name: 'freeSpace', stat: '24%' },
])

const systemHealth = ref(null)
const healthCheckInterval = ref(null)

/**
 * Determines if health data has component information
 */
const hasComponents = computed(() => {
  return systemHealth.value?.components &&
         Object.keys(systemHealth.value.components).length > 0
})

/**
 * Gets appropriate color class for status
 * @param {string} status - Component status string
 * @returns {string} CSS class for status
 */
const getStatusColor = (status) => {
  const colors = {
    'ready': 'bg-green-100 text-green-800',
    'disabled': 'bg-gray-100 text-gray-800',
    'error': 'bg-red-100 text-red-800',
    'warning': 'bg-yellow-100 text-yellow-800'
  }
  return colors[status] || 'bg-gray-100 text-gray-800'
}

/**
 * Formats a UNIX timestamp to localized date/time string
 * @param {number} timestamp - UNIX timestamp
 * @returns {string} Localized date/time string
 */
const formatTimestamp = (timestamp) => {
  return new Date(timestamp * 1000).toLocaleString()
}

/**
 * Fetch system health status from the server
 */
const checkHealth = async () => {
  try {
    console.log('Fetching health status...')
    const response = await dataService.checkHealth()

    if (!response.components) {
      console.warn('No components found in health response')
    }
    systemHealth.value = response
  } catch (error) {
    console.error('Error checking health status:', error)
  }
}

// Component lifecycle hooks
onMounted(() => {
  checkHealth()
  // Health check polling interval (30 seconds)
  healthCheckInterval.value = setInterval(checkHealth, 30000)
})

onUnmounted(() => {
  if (healthCheckInterval.value) {
    clearInterval(healthCheckInterval.value)
  }
})
</script>
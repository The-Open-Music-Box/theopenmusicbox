<template>
    <div class="space-y-6">
      <!-- Informations Générales -->
      <div>
        <h3 class="text-base font-semibold leading-6 text-gray-900">Informations Générales</h3>
        <dl class="mt-5 grid grid-cols-1 gap-5 sm:grid-cols-3">
          <div v-for="item in stats" :key="item.name"
            class="overflow-hidden rounded-lg bg-white px-4 py-5 shadow sm:p-6">
            <dt class="truncate text-sm font-medium text-gray-500">{{ item.name }}</dt>
            <dd class="mt-1 text-3xl font-semibold tracking-tight text-gray-900">{{ item.stat }}</dd>
          </div>
        </dl>
      </div>
  
      <!-- État du Système -->
      <div>
        <div class="flex items-center justify-between">
          <h3 class="text-base font-semibold leading-6 text-gray-900">État du Système</h3>
          <span :class="[
            'px-2 py-1 text-xs font-medium rounded-full',
            systemHealth?.status === 'healthy' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
          ]">
            {{ systemHealth?.status || 'unknown' }}
          </span>
        </div>
  <!-- Debug Info -->
  <div v-if="!hasComponents" class="mt-4 p-4 bg-yellow-50 text-yellow-700 rounded">
        Aucun composant trouvé dans les données de santé du système
      </div>
        <!-- Grille des Composants -->
        <div class="mt-5 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          <div v-for="(component, name) in systemHealth?.components" 
               :key="name"
               class="flex flex-col rounded-lg bg-white shadow">
            <div class="flex items-center justify-between p-4 border-b border-gray-200">
              <h4 class="text-sm font-medium text-gray-900 capitalize">{{ name }}</h4>
              <span :class="[
                'px-2 py-1 text-xs font-medium rounded-full',
                getStatusColor(component.status)
              ]">
                {{ component.status }}
              </span>
            </div>
            <div class="p-4">
              <p class="text-xs text-gray-500">
                Dernière mise à jour: {{ formatTimestamp(component.timestamp) }}
              </p>
            </div>
          </div>
        </div>
      </div>
      <!-- Debug Output -->
    <!-- <pre v-if="isDevelopment" class="mt-4 p-4 bg-gray-100 rounded text-xs overflow-auto">
      {{ JSON.stringify(systemHealth, null, 2) }}
    </pre> -->
    </div>
  </template>
  
  <script setup>
  import { ref, computed, onMounted, onUnmounted } from 'vue'
  import dataService from '../services/dataService'
  
  const stats = ref([
    { name: 'baterie', stat: '71%' },
    { name: 'nombre de musique', stat: '12' },
    { name: 'espace libre', stat: '24%' },
  ])
  
  const systemHealth = ref(null)
  const healthCheckInterval = ref(null)
  const isDevelopment = process.env.NODE_ENV === 'development'

const hasComponents = computed(() => {
  return systemHealth.value?.components && 
         Object.keys(systemHealth.value.components).length > 0
})
  const getStatusColor = (status) => {
    const colors = {
      'ready': 'bg-green-100 text-green-800',
      'disabled': 'bg-gray-100 text-gray-800',
      'error': 'bg-red-100 text-red-800',
      'warning': 'bg-yellow-100 text-yellow-800'
    }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }
  
  const formatTimestamp = (timestamp) => {
    return new Date(timestamp * 1000).toLocaleString()
  }
  
  const checkHealth = async () => {
    try {
        console.log('Fetching health status...')
      const response = await dataService.checkHealth()
      console.log('Health status response:', response)
    
    if (!response.components) {
      console.warn('No components found in health response')
    }
      systemHealth.value = response
    } catch (error) {
      console.error('Erreur lors de la vérification de santé:', error)
    }
  }
  
  onMounted(() => {
  console.log('StatsInfo component mounted')
  checkHealth()
  healthCheckInterval.value = setInterval(checkHealth, 30000)
})

  
  onUnmounted(() => {
    if (healthCheckInterval.value) {
      clearInterval(healthCheckInterval.value)
    }
  })
  </script>
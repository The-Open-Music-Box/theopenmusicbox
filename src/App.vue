<template>
  <div class="min-h-full">
    <HeaderNavigation />
    <router-view />
  </div>
  <div id="app">
    <div
      v-if="socketError"
      :class="['bg-error bg-opacity-10', 'border', 'border-error', 'text-error', 'px-4 py-3 rounded relative']"
      role="alert"
    >
      <strong class="font-bold">{{ t('common.socketError') }}</strong>
      <span class="block sm:inline"> {{ t('common.fallbackToMock') }}</span>
    </div>

  </div>
</template>

<script setup>
/**
 * App Component - Application Root
 *
 * The main entry point for the application.
 * Sets up global structure and socket connection state.
 */
import HeaderNavigation from './components/HeaderNavigation.vue'
import { onMounted, onUnmounted, ref, getCurrentInstance } from 'vue'
import { useI18n } from 'vue-i18n'
import { colors, getColor } from '@/theme/colors'

const { t } = useI18n()
const { proxy } = getCurrentInstance()
const socketError = ref(false)



/**
 * Set up socket event listeners
 */
const setupSocketListeners = () => {
  proxy.$socketService.on('response', (data) => {
    console.log('Received response from server:', data)
  })

  proxy.$socketService.on('connect_error', (error) => {
    console.error('Socket connection error:', error)
    socketError.value = true
  })
}

// Component lifecycle hooks
onMounted(() => {
  setupSocketListeners()
})

onUnmounted(() => {
  if (proxy.$socketService.disconnect) {
    proxy.$socketService.disconnect()
  }
})
</script>

<style lang="scss">
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: v-bind('colors.light.onBackground')
}
</style>
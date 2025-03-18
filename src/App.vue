<template>
  <div class="min-h-full">
    <HeaderNavigation />
    <router-view />
  </div>
  <div id="app">
    <div
      v-if="socketError"
      :class="[colors.error.background, colors.error.border, colors.error.text, 'px-4 py-3 rounded relative']"
      role="alert"
    >
      <strong class="font-bold">{{ $t('common.socketError') }}</strong>
      <span class="block sm:inline"> {{ $t('common.fallbackToMock') }}</span>
    </div>
    <button
      @click="sendMessage"
      :class="[colors.primary.main, 'mt-4 px-4 py-2 text-white rounded hover:' + colors.background.primary.main]"
    >
      {{ $t('common.sendMessage') }}
    </button>
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
import { i18n } from '@/i18n'
import { colors } from '@/theme/colors'

const { t: $t } = i18n
const { proxy } = getCurrentInstance()
const socketError = ref(false)

/**
 * Send a test message through the socket connection
 */
const sendMessage = () => {
  try {
    proxy.$socketService.emit('message', 'Hello, server!')
    console.log('Message sent to server')
  } catch (error) {
    console.error('Error sending message:', error)
    socketError.value = true
  }
}

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
  color: #2c3e50;
}
</style>
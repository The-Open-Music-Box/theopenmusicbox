<template>
  <div class="min-h-full">
    <HeaderNavigation />
    <router-view />
  </div>
  <div id="app">
    <div v-if="socketError" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
      <strong class="font-bold">Socket Connection Error!</strong>
      <span class="block sm:inline"> Unable to connect to the server. Using mock data instead.</span>
    </div>
    <button @click="sendMessage">Send Message</button>
  </div>
</template>

<script setup>
import HeaderNavigation from './components/HeaderNavigation.vue'
import { onMounted, onUnmounted, ref, getCurrentInstance } from 'vue'

const { proxy } = getCurrentInstance()
const socketError = ref(false)

const sendMessage = () => {
  try {
    proxy.$socketService.emit('message', 'Hello, server!')
    console.log('Sent message to server')
  } catch (error) {
    console.error('Error sending message:', error)
    socketError.value = true
  }
}

// Setup socket listeners
const setupSocketListeners = () => {
  proxy.$socketService.on('response', (data) => {
    console.log('Received response from server:', data)
  })

  proxy.$socketService.on('connect_error', (error) => {
    console.error('Socket connection error:', error)
    socketError.value = true
  })
}

onMounted(() => {
  console.log('Component mounted')
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

nav {
  padding: 30px;

  a {
    font-weight: bold;
    color: #2c3e50;

    &.router-link-exact-active {
      color: #42b983;
    }
  }
}
</style>
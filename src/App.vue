<template>
  <div class="min-h-full">
    <HeaderNavigation />
    <router-view />
  </div>
  <div id="app">
    <button @click="sendMessage">Send Message</button>
  </div>
</template>

<script setup>
import HeaderNavigation from './components/HeaderNavigation.vue'
import { onMounted, getCurrentInstance } from 'vue'

const { proxy } = getCurrentInstance()

const sendMessage = () => {
  proxy.$socketService.emit('message', 'Hello, server!')
  console.log('Sent message to server')
}

proxy.$socketService.on('response', (data) => {
  console.log('Received response from server:', data)
})

onMounted(() => {
  console.log('Component mounted')
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
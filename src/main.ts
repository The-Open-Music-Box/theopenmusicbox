import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import { i18n } from './i18n'
import './registerServiceWorker'
import router from './router'
import './assets/tailwind.css'
import socketService from './services/socketService'

const app = createApp(App)
const pinia = createPinia()

// Initialize Socket.IO connection
socketService.setupSocketConnection()

// Add Socket.IO service to Vue global properties
app.config.globalProperties.$socketService = socketService

app.use(pinia)
app.use(i18n)
app.use(router).mount('#app')

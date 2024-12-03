import { createApp } from 'vue'
import App from './App.vue'
import './registerServiceWorker'
import router from './router'
import './assets/tailwind.css'
import socketService from './services/socketService'

const app = createApp(App)

// Initialiser la connexion Socket.IO
socketService.setupSocketConnection()

// Ajouter le service Socket.IO aux propriétés globales de l'application Vue
app.config.globalProperties.$socketService = socketService

app.use(router).mount('#app')

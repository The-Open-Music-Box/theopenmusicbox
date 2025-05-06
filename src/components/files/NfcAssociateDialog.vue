<template>
  <div v-if="open" class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
    <div class="bg-white rounded-lg shadow-lg p-8 w-full max-w-md relative">
      <button class="absolute top-2 right-2 text-gray-400 hover:text-gray-700" @click="handleCancel">
        <span class="sr-only">Close</span>
        <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
      <h2 class="text-xl font-semibold mb-4 text-gray-800">Associer un tag NFC</h2>
      <div v-if="state === 'idle'">
        <p>Prêt à associer un tag NFC à la playlist.</p>
        <button class="btn-primary mt-4 w-full" @click="startAssociation">Démarrer</button>
      </div>
      <div v-else-if="state === 'waiting'">
        <p class="flex items-center gap-2 text-blue-600">
          <svg class="animate-spin h-5 w-5 text-blue-600" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/></svg>
          En attente d'un tag NFC...
        </p>
        <button class="btn-secondary mt-4 w-full" @click="handleCancel">Annuler</button>
      </div>
      <div v-else-if="state === 'success'">
        <p class="text-green-600 font-medium">Tag NFC associé avec succès !</p>
        <button class="btn-primary mt-4 w-full" @click="handleClose">Fermer</button>
      </div>
      <div v-else-if="state === 'already_linked'">
        <p class="text-yellow-600 font-medium">Ce tag NFC est déjà associé à une autre playlist.</p>
        <button class="btn-warning mt-4 w-full" @click="overrideAssociation">Forcer l'association</button>
        <button class="btn-secondary mt-2 w-full" @click="handleCancel">Annuler</button>
      </div>
      <div v-else-if="state === 'hardware_error'">
        <p class="text-red-600 font-medium">Erreur matérielle avec le lecteur NFC : {{ t('nfc.' + (errorMsg || 'NFC_NOT_AVAILABLE')) }}</p>
        <button class="btn-secondary mt-4 w-full" @click="handleCancel">Fermer</button>
      </div>
      <div v-else-if="state === 'nfc_unavailable'">
        <p class="text-red-600 font-medium">{{ t('nfc.' + (errorMsg || 'NFC_NOT_AVAILABLE')) }}</p>
        <button class="btn-secondary mt-4 w-full" @click="handleClose">Fermer</button>
      </div>
      <div v-else-if="state === 'error'">
        <p class="text-red-600 font-medium">Erreur lors de l'association du tag NFC.</p>
        <button class="btn-secondary mt-4 w-full" @click="handleCancel">Fermer</button>
      </div>
      <div v-else-if="state === 'cancelled'">
        <p class="text-gray-500">Association annulée.</p>
        <button class="btn-secondary mt-4 w-full" @click="handleClose">Fermer</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import socketService from '@/services/socketService'
import axios from 'axios'

const props = defineProps<{
  open: boolean,
  playlistId: string | null
}>()
const emit = defineEmits(['close', 'success'])

const state = ref<'idle' | 'waiting' | 'success' | 'already_linked' | 'error' | 'hardware_error' | 'cancelled' | 'nfc_unavailable'>('idle')
const errorMsg = ref<string | null>(null)

const { t } = useI18n()

// Socket.IO event handlers
function setupSocketHandlers() {
  socketService.on('nfc_waiting', () => { state.value = 'waiting' })
  socketService.on('nfc_link_success', () => { state.value = 'success'; emit('success') })
  socketService.on('nfc_tag_already_linked', () => { state.value = 'already_linked' })
  socketService.on('nfc_link_error', () => { state.value = 'error' })
  socketService.on('nfc_cancelled', () => { state.value = 'cancelled' })
}
function cleanupSocketHandlers() {
  socketService.off('nfc_waiting')
  socketService.off('nfc_link_success')
  socketService.off('nfc_tag_already_linked')
  socketService.off('nfc_link_error')
  socketService.off('nfc_cancelled')
}

watch(() => props.open, async (newVal) => {
  if (newVal) {
    // Vérifie le statut NFC au chargement du popup
    try {
      const res = await axios.get('/health')
      if (res.data?.nfc && res.data.nfc.available === false) {
        state.value = 'nfc_unavailable'
        errorMsg.value = res.data.nfc.code
        return
      }
    } catch (e) {
      // Si l'appel health échoue, fallback sur erreur hardware
      state.value = 'hardware_error'
      errorMsg.value = 'NFC_NOT_AVAILABLE'
      return
    }
    state.value = 'idle'
    setupSocketHandlers()
  } else {
    cleanupSocketHandlers()
  }
})
onUnmounted(cleanupSocketHandlers)

const startAssociation = async () => {
  if (!props.playlistId) return
  state.value = 'waiting'
  try {
    await axios.post('/api/nfc/observe', { playlist_id: props.playlistId })
    // Attente des événements socket pour la suite
  } catch (err: any) {
    // Gestion de l’erreur hardware NFC
    if (err?.response?.status === 503 || (typeof err?.response?.data?.error === 'string' && err.response.data.error.toLowerCase().includes('hardware'))) {
      state.value = 'hardware_error'
      errorMsg.value = err.response?.data?.error || 'Erreur matérielle avec le lecteur NFC.'
    } else {
      state.value = 'error'
    }
  }
}

const overrideAssociation = async () => {
  if (!props.playlistId) return
  try {
    await axios.post('/api/nfc/link', { playlist_id: props.playlistId, override: true })
    // Attente des événements socket pour la suite
  } catch (err) {
    state.value = 'error'
  }
}

const handleCancel = async () => {
  try {
    await axios.post('/api/nfc/cancel')
  } catch {
    // Silence error: l'utilisateur peut annuler même si la requête échoue
  }
  state.value = 'cancelled'
  emit('close')
}
const handleClose = () => {
  emit('close')
}
</script>

<style scoped>
.btn-primary {
  @apply bg-blue-600 text-white rounded px-4 py-2 font-semibold hover:bg-blue-700;
}
.btn-secondary {
  @apply bg-gray-200 text-gray-700 rounded px-4 py-2 font-semibold hover:bg-gray-300;
}
.btn-warning {
  @apply bg-yellow-400 text-gray-900 rounded px-4 py-2 font-semibold hover:bg-yellow-500;
}
</style>

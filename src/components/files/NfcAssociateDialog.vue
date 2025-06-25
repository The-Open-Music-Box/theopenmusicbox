<template>
  <div v-if="open" class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
    <div class="bg-white rounded-lg shadow-lg p-8 w-full max-w-md relative">
      <button class="absolute top-2 right-2 text-disabled hover:text-onBackground" @click="handleCancel">
        <span class="sr-only">Close</span>
        <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
      <h2 class="text-xl font-semibold mb-4 text-onBackground">{{ t('nfc.associate_tag') }}</h2>

      <!-- Initial state - ready to start association -->
      <div v-if="state === 'idle'">
        <p>{{ t('nfc.ready_to_associate') }}</p>
        <button class="btn-primary mt-4 w-full" @click="startAssociation">{{ t('nfc.start') }}</button>
      </div>

      <!-- Waiting for tag scan -->
      <div v-else-if="state === 'waiting'">
        <div class="mb-4">
          <p class="flex items-center gap-2 text-primary mb-2">
            <svg class="animate-spin h-5 w-5 text-primary" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/></svg>
            {{ t('nfc.waiting_for_tag') }}
          </p>
          <div v-if="scanStatus" class="text-sm text-disabled italic">
            {{ t('nfc.scanning_status') }}: {{ scanStatus }}
          </div>
        </div>
        <button class="btn-secondary mt-4 w-full" @click="handleCancel">{{ t('common.cancel') }}</button>
      </div>

      <!-- Tag successfully associated -->
      <div v-else-if="state === 'success'">
        <div class="flex items-center gap-2 text-success font-medium mb-2">
          <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
          {{ t('nfc.tag_associated_success') }}
        </div>
        <p v-if="nfcStatusMessage" class="text-sm text-disabled mt-2 mb-4">{{ nfcStatusMessage }}</p>
        <button class="btn-primary mt-4 w-full" @click="handleClose">{{ t('common.close') }}</button>
      </div>

      <!-- Tag already associated with another playlist -->
      <div v-else-if="state === 'already_associated'">
        <div class="flex items-center gap-2 text-warning font-medium mb-2">
          <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          {{ t('nfc.tag_already_associated') }}
        </div>
        <p v-if="nfcStatusMessage" class="text-sm text-disabled mt-2 mb-4">{{ nfcStatusMessage }}</p>
        <button class="btn-warning mt-4 w-full" @click="overrideAssociation">{{ t('nfc.force_association') }}</button>
        <button class="btn-secondary mt-2 w-full" @click="handleCancel">{{ t('common.cancel') }}</button>
      </div>

      <!-- Hardware error with NFC reader -->
      <div v-else-if="state === 'hardware_error'">
        <div class="flex items-center gap-2 text-error font-medium mb-2">
          <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {{ t('nfc.hardware_error') }}
        </div>
        <p class="text-sm text-disabled mt-2">{{ t('nfc.' + (errorMsg || 'NFC_NOT_AVAILABLE')) }}</p>
        <button class="btn-secondary mt-4 w-full" @click="handleCancel">{{ t('common.close') }}</button>
      </div>

      <!-- NFC unavailable -->
      <div v-else-if="state === 'nfc_unavailable'">
        <div class="flex items-center gap-2 text-error font-medium mb-2">
          <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
          </svg>
          {{ t('nfc.unavailable') }}
        </div>
        <p class="text-sm text-disabled mt-2">{{ t('nfc.' + (errorMsg || 'NFC_NOT_AVAILABLE')) }}</p>
        <button class="btn-secondary mt-4 w-full" @click="handleClose">{{ t('common.close') }}</button>
      </div>

      <!-- General error -->
      <div v-else-if="state === 'error'">
        <div class="flex items-center gap-2 text-error font-medium mb-2">
          <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
          {{ t('nfc.association_error') }}
        </div>
        <p v-if="errorMsg" class="text-sm text-disabled mt-2">{{ errorMsg }}</p>
        <button class="btn-secondary mt-4 w-full" @click="handleCancel">{{ t('common.close') }}</button>
      </div>

      <!-- Association cancelled -->
      <div v-else-if="state === 'cancelled'">
        <p class="text-disabled">{{ t('nfc.association_cancelled') }}</p>
        <button class="btn-secondary mt-4 w-full" @click="handleClose">{{ t('common.close') }}</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import socketService from '@/services/socketService'
import api from '@/services/api'

const props = defineProps<{
  open: boolean,
  playlistId: string | null
}>()
const emit = defineEmits(['close', 'success'])

// State management
const state = ref<'idle' | 'waiting' | 'success' | 'already_associated' | 'error' | 'hardware_error' | 'cancelled' | 'cancelling' | 'nfc_unavailable'>('idle')
const errorMsg = ref<string | null>(null)
const nfcStatusMessage = ref<string | null>(null)
const scanStatus = ref<string | null>(null)
const associatedPlaylistInfo = ref<{id: string, title: string} | null>(null)
const lastTagId = ref<string | null>(null)

const { t } = useI18n()

// Socket.IO event handlers
function setupSocketHandlers() {
  // Handle NFC status updates
  socketService.on('nfc_status', (data) => {
    console.log('NFC status:', data)
    const status = data.status

    switch (status) {
      case 'waiting':
        state.value = 'waiting'
        nfcStatusMessage.value = data.message || t('nfc.waiting_for_tag')
        break

      case 'already_associated':
        state.value = 'already_associated'
        nfcStatusMessage.value = data.message || t('nfc.tag_used_by_other_playlist')
        if (data.associated_playlist_id && data.associated_playlist_title) {
          associatedPlaylistInfo.value = {
            id: data.associated_playlist_id,
            title: data.associated_playlist_title
          }
        }
        if (data.tag_id) {
          lastTagId.value = data.tag_id
        }
        break

      case 'success':
        state.value = 'success'
        nfcStatusMessage.value = data.message || t('nfc.tag_associated_success')
        // Only emit success signal but don't close, wait for user to click OK
        // The dialog will stay open until user clicks the button
        emit('success', { closeDialog: false }) // Explicitly indicate not to close
        break

      case 'error':
        state.value = 'error'
        errorMsg.value = data.message || t('nfc.general_error')
        break

      case 'stopped':
      case 'not_listening':
        // Only transition to cancelled if we're not already in a completion state
        if (state.value === 'waiting') {
          state.value = 'cancelled'
        }
        break

      case 'override_mode':
        // When override mode is enabled, update the UI to show we're processing
        nfcStatusMessage.value = data.message || t('nfc.override_in_progress')
        break
    }
  })

  // Handle real-time scanning updates
  socketService.on('nfc_scanning', (data) => {
    scanStatus.value = new Date().toLocaleTimeString()
    if (data.last_tag_id) {
      lastTagId.value = data.last_tag_id
    }
  })

  // Handle tag detection events
  socketService.on('nfc_tag_detected', (data) => {
    console.log('NFC tag detected:', data)
    if (data.tag_id) {
      lastTagId.value = data.tag_id
      scanStatus.value = new Date().toLocaleTimeString() + ` - Tag: ${data.tag_id}`
    }
  })

  // Handle errors
  socketService.on('nfc_error', (data) => {
    console.error('NFC error:', data)
    state.value = 'error'
    errorMsg.value = data.message || t('nfc.general_error')
  })
}

function cleanupSocketHandlers() {
  socketService.off('nfc_status')
  socketService.off('nfc_scanning')
  socketService.off('nfc_tag_detected')
  socketService.off('nfc_error')
}

watch(() => props.open, async (newVal) => {
  if (newVal) {
    // Vérifie le statut NFC au chargement du popup
    try {
      const data = await api.get('/api/health')
      if (data?.nfc && data.nfc.available === false) {
        state.value = 'nfc_unavailable'
        errorMsg.value = data.nfc.code
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

  // Reset state variables
  scanStatus.value = null
  nfcStatusMessage.value = null
  lastTagId.value = null
  associatedPlaylistInfo.value = null

  // Set initial waiting state
  state.value = 'waiting'

  try {
    console.log('Starting NFC association for playlist:', props.playlistId)

    // Emit Socket.IO event to start NFC listening
    socketService.emit('start_nfc_link', { playlist_id: props.playlistId })

    // Status updates will be handled by socket event handlers
  } catch (err: any) {
    console.error('Error starting NFC association:', err)

    // Handle hardware errors
    if (err?.response?.status === 503 ||
        (typeof err?.response?.data?.error === 'string' &&
         err.response.data.error.toLowerCase().includes('hardware'))) {
      state.value = 'hardware_error'
      errorMsg.value = err.response?.data?.error || t('nfc.hardware_error_details')
    } else {
      state.value = 'error'
      errorMsg.value = err?.message || t('nfc.general_error')
    }
  }
}

const overrideAssociation = async () => {
  if (!props.playlistId) return
  try {
    // Emit Socket.IO event to override existing association
    socketService.emit('override_nfc_tag', {})

    // Status updates will be handled by socket event handlers
  } catch (err: any) {
    console.error('Error overriding NFC association:', err)
    state.value = 'error'
    errorMsg.value = err?.message || t('nfc.override_error')
  }
}

const handleCancel = async () => {
  try {
    // Emit Socket.IO event to cancel NFC association
    socketService.emit('stop_nfc_link', {})
    console.log('Sent stop_nfc_link event')

    // Update state but wait for confirmation from server before closing
    state.value = 'cancelling'
    nfcStatusMessage.value = t('nfc.cancelling_association')
  } catch (err) {
    console.error('Error cancelling NFC association:', err)
    // User can still cancel even if the request fails
    state.value = 'cancelled'
    emit('close')
  }
}
const handleClose = async () => {
  try {
    // When closing the dialog, always ensure NFC association mode is stopped
    socketService.emit('stop_nfc_link', {})
    console.log('Sent stop_nfc_link event from handleClose')
  } catch (err) {
    console.error('Error stopping NFC association on dialog close:', err)
  } finally {
    // Always close the dialog
    emit('close')
  }
}
</script>

<style scoped>
.btn-primary {
  @apply bg-primary text-onPrimary rounded px-4 py-2 font-semibold hover:bg-primary-light;
}
.btn-secondary {
  @apply bg-surface text-onSurface rounded px-4 py-2 font-semibold hover:bg-background;
}
.btn-warning {
  @apply bg-warning text-onWarning rounded px-4 py-2 font-semibold hover:bg-warning-light;
}
</style>

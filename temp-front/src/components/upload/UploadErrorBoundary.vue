<template>
  <div>
    <slot 
      :upload-with-error-handling="uploadWithErrorHandling"
      :is-error-boundary-active="isErrorBoundaryActive"
    />
    
    <!-- Error notification -->
    <div 
      v-if="showErrorNotification" 
      class="fixed bottom-4 right-4 bg-red-500 text-white p-4 rounded-lg shadow-lg z-50 max-w-md"
    >
      <div class="flex justify-between items-start">
        <div>
          <h4 class="font-semibold">Upload Error</h4>
          <p class="text-sm">{{ lastError }}</p>
        </div>
        <button 
          @click="showErrorNotification = false"
          class="text-white hover:text-gray-200"
        >
          ×
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'

const isErrorBoundaryActive = ref(false)
const showErrorNotification = ref(false)
const lastError = ref('')

// Intercepter les erreurs JavaScript globales
const handleGlobalError = (event: ErrorEvent) => {
  console.error('🚨 [UploadErrorBoundary] Global error caught:', event.error)
  lastError.value = event.message || 'Unknown error occurred'
  showErrorNotification.value = true
  
  // Empêcher la propagation qui pourrait causer un refresh
  event.preventDefault()
  return false
}

// Intercepter les rejets de promesses non gérés
const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
  console.error('🚨 [UploadErrorBoundary] Unhandled promise rejection:', event.reason)
  lastError.value = `Promise rejection: ${event.reason}`
  showErrorNotification.value = true
  
  // Empêcher la propagation qui pourrait causer un refresh
  event.preventDefault()
}

// Wrapper sécurisé pour les opérations d'upload
const uploadWithErrorHandling = async (uploadFunction: () => Promise<void>) => {
  isErrorBoundaryActive.value = true
  
  try {
    await uploadFunction()
  } catch (error: unknown) {
    console.error('🚨 [UploadErrorBoundary] Upload operation failed:', error)
    lastError.value = error instanceof Error ? error.message : 'Upload failed'
    showErrorNotification.value = true
    
    // Ne pas propager l'erreur pour éviter des refreshs
    return
  } finally {
    isErrorBoundaryActive.value = false
  }
}

onMounted(() => {
  // Ajouter les gestionnaires d'erreurs globaux
  window.addEventListener('error', handleGlobalError)
  window.addEventListener('unhandledrejection', handleUnhandledRejection)
})

onBeforeUnmount(() => {
  // Nettoyer les gestionnaires d'erreurs
  window.removeEventListener('error', handleGlobalError)
  window.removeEventListener('unhandledrejection', handleUnhandledRejection)
})

defineExpose({
  uploadWithErrorHandling
})
</script>

// components/files/FileListContainer.vues
<template>
  <div>
    <!-- Ajout de la gestion du chargement et des erreurs -->
    <div v-if="isLoading" class="text-gray-600">Chargement...</div>
    <div v-if="error" class="text-red-600">{{ error }}</div>
    
    <template v-if="!isLoading && !error">
      <FilesListHeader />
      <FilesList :files="files" />
      <!-- Utilisation directe de DeleteDialog -->
      <DeleteDialog 
        :open="showDeleteDialog" 
        :file="selectedFile" 
        @close="closeDeleteDialog"
        @confirm="handleDeleteConfirm" 
      />
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useFilesStore } from '../files/composables/useFilesStore'
import { useFileDialog } from '../files/composables/useFileDialog'
import FilesListHeader from './FilesListHeader.vue'
import FilesList from './FilesList.vue'
import DeleteDialog from '../DeleteDialog.vue'
import { AudioFile, FileStatus } from '../files/types' 

// Utilisation des deux composables séparés
const { files, isLoading, error, loadFiles, deleteFile } = useFilesStore()
const { showDeleteDialog, selectedFile, closeDeleteDialog } = useFileDialog()

// Gestion de la suppression
const handleDeleteConfirm = async () => {
  if (!selectedFile.value) return
  try {
    await deleteFile(selectedFile.value.id)
    closeDeleteDialog()
  } catch (err) {
    // L'erreur est déjà gérée dans le store
  }
}

onMounted(loadFiles)
</script>
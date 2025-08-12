import { ref, computed, onUnmounted } from 'vue';
import dataService from '../../../services/dataService';
import socketService from '../../../services/socketService';
import { SOCKET_EVENTS } from '../../../constants/apiRoutes';
import { useI18n } from 'vue-i18n';

/**
 * Default chunk size for file uploads (1MB)
 */
const CHUNK_SIZE = 1024 * 1024;

/**
 * Maximum number of retry attempts when a chunk upload fails
 */
const MAX_RETRY_ATTEMPTS = 3;

/**
 * Composable for managing chunked file uploads with progress tracking,
 * retry logic, and Socket.IO real-time progress updates
 */
export function useChunkedUpload() {
  const { t } = useI18n();
  
  // État
  const uploadFiles = ref<File[]>([]);
  const uploadProgress = ref(0);
  const isUploading = ref(false);
  const uploadErrors = ref<string[]>([]);
  const currentSessionId = ref<string | null>(null);
  const currentFileIndex = ref(0);
  const currentChunkIndex = ref(0);
  const totalChunks = ref(0);
  const currentFileName = ref<string | null>(null);
  const currentPlaylistId = ref<string | null>(null); // Référence stable pour le playlistId
  
  // Statistiques d'upload
  const stats = ref({
    startTime: 0,
    bytesUploaded: 0,
    totalBytes: 0,
    speed: 0, // bytes/second
  });
  
  // Temps restant estimé (en secondes)
  const estimatedTimeRemaining = computed(() => {
    if (stats.value.speed === 0) return 0;
    const remainingBytes = stats.value.totalBytes - stats.value.bytesUploaded;
    return Math.round(remainingBytes / stats.value.speed);
  });
  
  // Configurer les écouteurs d'événements Socket.IO
  const setupSocketListeners = () => {
    // Supprimer les anciens écouteurs pour éviter les doublons
    cleanupSocketListeners();
    socketService.on(SOCKET_EVENTS.UPLOAD_PROGRESS, (data) => {
      if (data.session_id === currentSessionId.value) {
        uploadProgress.value = data.progress;
        currentChunkIndex.value = data.chunk_index + 1;
      }
    });
    
    socketService.on(SOCKET_EVENTS.UPLOAD_COMPLETE, (data) => {
      if (data.session_id === currentSessionId.value) {
        uploadProgress.value = 100;
        // Passer au fichier suivant ou terminer
        currentFileIndex.value++;
        if (currentFileIndex.value >= uploadFiles.value.length) {
          isUploading.value = false;
          uploadFiles.value = [];
          currentFileName.value = null;
        } else {
          // Démarrer l'upload du fichier suivant
          uploadNextFile();
        }
      }
    });
    
    socketService.on(SOCKET_EVENTS.UPLOAD_ERROR, (data) => {
      if (data.session_id === currentSessionId.value) {
        uploadErrors.value.push(data.error || t('upload.unknownError'));
        isUploading.value = false;
      }
    });
  };

  // Nettoyer les écouteurs Socket.IO
  const cleanupSocketListeners = () => {
    socketService.off(SOCKET_EVENTS.UPLOAD_PROGRESS);
    socketService.off(SOCKET_EVENTS.UPLOAD_COMPLETE);
    socketService.off(SOCKET_EVENTS.UPLOAD_ERROR);
  };
  
  // Découper un fichier en chunks
  const sliceFile = (file: File, chunkIndex: number) => {
    const start = chunkIndex * CHUNK_SIZE;
    const end = Math.min(start + CHUNK_SIZE, file.size);
    return file.slice(start, end);
  };
  
  // Générer un checksum pour un fichier ou un blob
  const generateChecksum = async (file: File | Blob): Promise<string> => {
    const buffer = await file.arrayBuffer();
    const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
    return Array.from(new Uint8Array(hashBuffer))
      .map(b => b.toString(16).padStart(2, '0'))
      .join('');
  };
  
  // Uploader un chunk avec gestion de retry
  const uploadChunkWithRetry = async (
    playlistId: string, 
    formData: FormData, 
    chunkIndex: number, 
    retryCount = 0
  ): Promise<boolean> => {
    try {
      await dataService.uploadChunk(playlistId, formData);
      return true;
    } catch (error: any) {
      console.warn(`Upload chunk ${chunkIndex} failed (attempt ${retryCount + 1}/${MAX_RETRY_ATTEMPTS}):`, error);
      
      // Si nous avons atteint le nombre maximum de tentatives, propager l'erreur
      if (retryCount >= MAX_RETRY_ATTEMPTS - 1) {
        throw error;
      }
      
      // Attendre un court délai avant de réessayer (backoff exponentiel)
      const delayMs = Math.min(1000 * Math.pow(2, retryCount), 10000);
      await new Promise(resolve => setTimeout(resolve, delayMs));
      
      // Réessayer
      return uploadChunkWithRetry(playlistId, formData, chunkIndex, retryCount + 1);
    }
  };
  
  // Uploader un fichier par chunks
  const uploadNextFile = async () => {
    console.log('[DEBUG] uploadNextFile - Starting upload for playlist ID:', currentPlaylistId.value);
    
    if (!currentPlaylistId.value || currentFileIndex.value >= uploadFiles.value.length) {
      console.log('[DEBUG] uploadNextFile - No playlist ID or no files to upload');
      isUploading.value = false;
      return;
    }
    
    const file = uploadFiles.value[currentFileIndex.value];
    currentFileName.value = file.name;
    const totalFileChunks = Math.ceil(file.size / CHUNK_SIZE);
    totalChunks.value = totalFileChunks;
    
    console.log('[DEBUG] uploadNextFile - File details:', { 
      name: file.name, 
      size: file.size, 
      type: file.type,
      chunks: totalFileChunks 
    });
    
    try {
      // 1. Initialiser l'upload
      console.log('[DEBUG] uploadNextFile - Initializing upload with playlist ID:', currentPlaylistId.value);
      const initParams = {
        filename: file.name,
        total_size: file.size,
        total_chunks: totalFileChunks
      };
      console.log('[DEBUG] uploadNextFile - Init params:', initParams);
      
      const initResponse = await dataService.initUpload(currentPlaylistId.value, initParams);
      console.log('[DEBUG] uploadNextFile - Init response:', initResponse);
      
      currentSessionId.value = initResponse.session_id;
      currentChunkIndex.value = 0;
      
      // 2. Uploader les chunks
      for (let i = 0; i < totalFileChunks; i++) {
        if (!isUploading.value) {
          // L'upload a été annulé
          break;
        }
        
        const chunk = sliceFile(file, i);
        
        const formData = new FormData();
        formData.append('session_id', currentSessionId.value as string);
        formData.append('chunk_index', i.toString());
        
        // Créer un nouveau File à partir du Blob pour conserver le nom du fichier
        const chunkFile = new File([chunk], file.name, { type: file.type });
        formData.append('file', chunkFile);
        
        // Calculer un checksum pour le chunk
        const chunkChecksum = await generateChecksum(new Blob([chunk]));
        formData.append('checksum', chunkChecksum);
        
        // Upload avec retry automatique
        await uploadChunkWithRetry(currentPlaylistId.value, formData, i);
        currentChunkIndex.value = i + 1;
        
        // Mise à jour des statistiques
        stats.value.bytesUploaded += chunk.size;
        const elapsedTime = (Date.now() - stats.value.startTime) / 1000;
        if (elapsedTime > 0) {
          stats.value.speed = stats.value.bytesUploaded / elapsedTime;
        }
        
        // Mise à jour de la progression locale (en attendant les événements socket)
        uploadProgress.value = Math.round((i + 1) / totalFileChunks * 100);
      }
      
      if (isUploading.value) {
        // 3. Finaliser l'upload
        await dataService.finalizeUpload(currentPlaylistId.value, { 
          session_id: currentSessionId.value as string 
        });
      }
      
    } catch (error: any) {
      // Log error and update error state
      uploadErrors.value.push(`${t('upload.failedToUpload')} ${file.name}: ${error.message || t('upload.unknownError')}`);
      isUploading.value = false;
    }
  };
  
  // Démarrer l'upload de tous les fichiers
  const upload = async (playlistIdParam: string) => {
    // Start upload process for the specified playlist
    
    try {
      currentPlaylistId.value = playlistIdParam;
      isUploading.value = true;
      uploadProgress.value = 0;
      uploadErrors.value = [];
      currentFileIndex.value = 0;
      
      // Initialiser les statistiques
      stats.value = {
        startTime: Date.now(),
        bytesUploaded: 0,
        totalBytes: uploadFiles.value.reduce((total, file) => total + file.size, 0),
        speed: 0
      };
      
      // Configurer les écouteurs d'événements
      setupSocketListeners();
      
      // Démarrer l'upload du premier fichier
      await uploadNextFile();
      
    } catch (error: any) {
      // Log and handle upload failure
      uploadErrors.value.push(`${t('upload.uploadFailed')}: ${error.message || t('upload.unknownError')}`);
      isUploading.value = false;
    }
  };
  
  // Annuler l'upload en cours
  const cancelUpload = () => {
    isUploading.value = false;
    uploadFiles.value = [];
    currentSessionId.value = null;
    currentFileName.value = null;
    
    // Désactiver les écouteurs d'événements
    cleanupSocketListeners();
  };

  // S'assurer que les écouteurs sont nettoyés lorsque le composant est démonté
  onUnmounted(() => {
    if (isUploading.value) {
      cancelUpload();
    }
    cleanupSocketListeners();
  });
  
  return {
    uploadFiles,
    uploadProgress,
    isUploading,
    uploadErrors,
    estimatedTimeRemaining,
    stats,
    currentFileName,
    currentChunkIndex,
    totalChunks,
    upload,
    cancelUpload
  };
}

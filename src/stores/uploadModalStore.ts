import { reactive } from 'vue'

interface UploadModalState {
  isOpen: boolean
  currentPlaylistId: string | null
}

const state = reactive<UploadModalState>({
  isOpen: false,
  currentPlaylistId: null
})

export const useUploadModalStore = () => {
  const open = (playlistId: string) => {
    state.currentPlaylistId = playlistId
    state.isOpen = true
  }
  
  const close = () => {
    state.isOpen = false
    // Keep playlistId for a moment to allow cleanup
    setTimeout(() => {
      state.currentPlaylistId = null
    }, 300)
  }
  
  return {
    isOpen: () => state.isOpen,
    currentPlaylistId: () => state.currentPlaylistId,
    open,
    close
  }
}

<template>
  <div>
    <main class="pt-12">
      <div class="mx-auto max-w-7xl px-4 pb-12 sm:px-6 lg:px-8">
        <div class="rounded-lg bg-white px-5 py-6 shadow sm:px-6">
          <div class="app-container">
            <AudioPlayer
              :selectedTrack="selectedTrack"
              :playlist="selectedPlaylist"
            />
          </div>
          <div v-if="uploadProgress > 0" class="mt-4">
            <h4 class="sr-only">Status</h4>
            <p class="text-sm font-medium text-gray-900">Ajout du fichier sur le serveur...</p>
            <div class="mt-6" aria-hidden="true">
              <div class="overflow-hidden rounded-full bg-gray-200">
                <div class="h-2 rounded-full bg-indigo-600" :style="{ width: uploadProgress + '%' }"></div>
              </div>
              <div class="mt-6 hidden grid-cols-4 text-sm font-medium text-gray-600 sm:grid">
                <div class="text-indigo-600">Copie des fichiers</div>
              </div>
            </div>
          </div>
          <UploadForm />

          <FileListContainer
            :selectedTrack="selectedTrack"
            @select-track="handleSelectTrack"
          />


        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import AudioPlayer from '../components/audio/AudioPlayer.vue'
import UploadForm from '../components/upload/UploadFormContainer.vue'
import FileListContainer from '../components/files/FileListContainer.vue'
import GeneralInfo from '../components/StatsInfo.vue'
import type { Track, PlayList } from '../components/files/types'

const uploadProgress = ref(0)
const selectedTrack = ref<Track | null>(null)
const selectedPlaylist = ref<PlayList | null>(null)

const handleSelectTrack = (data: { track: Track, playlist: PlayList }) => {
  selectedTrack.value = data.track
  selectedPlaylist.value = data.playlist
}
</script>
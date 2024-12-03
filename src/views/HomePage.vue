<template>
  <div>
    <main class="pt-12">
      <div class="mx-auto max-w-7xl px-4 pb-12 sm:px-6 lg:px-8">
        <div class="rounded-lg bg-white px-5 py-6 shadow sm:px-6">
          <div class="app-container">
            <AudioPlayer />
          </div>
          <div v-if="uploadProgress > 0" class="mt-4">
            <h4 class="sr-only">Status</h4>
            <p class="text-sm font-medium text-gray-900">Adding your file on the server...</p>
            <div class="mt-6" aria-hidden="true">
              <div class="overflow-hidden rounded-full bg-gray-200">
                <div class="h-2 rounded-full bg-indigo-600" :style="{ width: uploadProgress + '%' }"></div>
              </div>
              <div class="mt-6 hidden grid-cols-4 text-sm font-medium text-gray-600 sm:grid">
                <div class="text-indigo-600">Copying files</div>
              </div>
            </div>
          </div>
          <UploadForm />
          <FilesList />
          <GeneralInfo />
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import AudioPlayer from '../components/AudioPlayer.vue'
import UploadForm from '../components/UploadForm.vue'
import FilesList from '../components/FilesList.vue'
import GeneralInfo from '../components/StatsInfo.vue'
import { ref } from 'vue'

const uploadProgress = ref(0)

</script>
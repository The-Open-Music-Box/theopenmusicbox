<template>
    <form @submit.prevent="confirmFileUpload">
        <div class="space-y-12 mt-20 mb-8">
            <div class="border-b border-gray-900/10 pb-12">
                <div class="mt-10 grid grid-cols-1 gap-x-6 gap-y-8 sm:grid-cols-6">
                    <div class="col-span-full">
                        <div
                            class="mt-2 flex justify-center rounded-lg border border-dashed border-gray-900/25 px-6 py-10">
                            <div class="text-center">
                                <PhotoIcon class="mx-auto h-12 w-12 text-gray-300" aria-hidden="true" />
                                <div class="mt-4 flex text-sm leading-6 text-gray-600">
                                    <label for="file-upload"
                                        class="relative cursor-pointer rounded-md bg-white font-semibold text-indigo-600 focus-within:outline-none focus-within:ring-2 focus-within:ring-indigo-600 focus-within:ring-offset-2 hover:text-indigo-500">
                                        <span>Upload a file</span>
                                        <input id="file-upload" name="file-upload" type="file" class="sr-only" multiple
                                            accept="*" @change="handleFileUpload" />
                                    </label>
                                    <p class="pl-1">or drag and drop</p>
                                </div>
                                <p class="text-xs leading-5 text-gray-600">Audio</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </form>
    <div class="mt-6" aria-hidden="true">
        <div class="overflow-hidden rounded-full bg-gray-200">
            <div class="h-2 rounded-full bg-indigo-600" :style="{ width: uploadProgress + '%' }"></div>
        </div>
        <div class="mt-6 hidden grid-cols-4 text-sm font-medium text-gray-600 sm:grid">
            <div class="text-indigo-600">Copying files</div>
        </div>
    </div>
</template>

<script setup>
import { ref, getCurrentInstance, onMounted } from 'vue'
import axios from 'axios'
import { PhotoIcon } from '@heroicons/vue/20/solid'

const { proxy } = getCurrentInstance()

const files = ref([])
const uploadProgress = ref(0)

const handleFileUpload = (event) => {
    console.log('handleFileUpload called')
    const selectedFiles = event.target.files
    const validFiles = []
    const maxSize = 1024 * 1024 * 1024
    const validAudioExtensions = 'audio/'
    console.log('Selected files:', selectedFiles)
    for (let i = 0; i < selectedFiles.length; i++) {
        const file = selectedFiles[i]
        if (file.type.startsWith(validAudioExtensions) && file.size <= maxSize) {
            validFiles.push(file)
            console.log('File added:', file.name)
        } else {
            alert(`Invalid file type or size: ${file.name} (Type: ${file.type}, Size: ${file.size} bytes)`)
        }
    }
    files.value = validFiles
    console.log('Valid files:', validFiles)
    if (validFiles.length > 0) {
        submitFiles()
    }
}

const confirmFileUpload = () => {
    console.log('Confirm file upload called')
    submitFiles()
}

const submitFiles = () => {
    const formData = new FormData()

    for (let i = 0; i < files.value.length; i++) {
        formData.append('files', files.value[i])

    }
    console.log('Submitting files:', files.value)
    axios
        .post('/api/upload', formData, {
            onUploadProgress: (progressEvent) => {
                uploadProgress.value = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            }

        })
        .then((response) => {
            console.log('Files uploaded successfully', response.data)
            files.value = []
            uploadProgress.value = 0
            proxy.$socketService.emit('audio_map_update', response.data)
        })
        .catch((error) => {
            console.error('There was an error!', error)
        })
}
onMounted(() => {
    console.log('Component Upload form mounted')
})
</script>
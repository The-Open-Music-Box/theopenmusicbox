<template>
    <div :key="componentKey">
        <p class="pl-1">List of files</p>
        <ul role="list" class="divide-y divide-gray-100">
            <li v-for="file in files" :key="file.id" class="flex items-center justify-between gap-x-6 py-5">
                <div class="min-w-0">
                    <div class="flex items-start gap-x-3">
                        <p class="text-sm font-semibold leading-6 text-gray-900">{{ file.name }}</p>
                        <p
                            :class="[statuses[file.status], 'rounded-md whitespace-nowrap mt-0.5 px-1.5 py-0.5 text-xs font-medium ring-1 ring-inset']">
                            {{ file.status }}</p>
                    </div>
                </div>
                <div class="flex flex-none items-center gap-x-4">
                    <button @click="openDialogUpload = true"
                        class="inline-flex w-full justify-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600">
                        Associer un tag
                    </button>
                    <Menu as="div" class="relative flex-none">
                        <MenuButton class="-m-2.5 block p-2.5 text-gray-500 hover:text-gray-900">
                            <span class="sr-only">Open options</span>
                            <EllipsisVerticalIcon class="h-5 w-5" aria-hidden="true" />
                        </MenuButton>
                        <transition enter-active-class="transition ease-out duration-100"
                            enter-from-class="transform opacity-0 scale-95"
                            enter-to-class="transform opacity-100 scale-100"
                            leave-active-class="transition ease-in duration-75"
                            leave-from-class="transform opacity-100 scale-100"
                            leave-to-class="transform opacity-0 scale-95">
                            <MenuItems
                                class="absolute right-0 z-10 mt-2 w-32 origin-top-right rounded-md bg-white py-2 shadow-lg ring-1 ring-gray-900/5 focus:outline-none">
                                <MenuItem v-slot="{ active }">
                                <button @click="showDeleteDialog(file)"
                                    :class="[active ? 'bg-gray-50' : '', 'block w-full text-left px-3 py-1 text-sm leading-6 text-gray-900']">
                                    Delete<span class="sr-only">, {{ file.name }}</span>
                                </button>
                                </MenuItem>
                            </MenuItems>
                        </transition>
                    </Menu>
                </div>
            </li>
        </ul>
        <DeleteDialog :open="openDialogDelete" :file="selectedFile" @close="openDialogDelete = false"
            @confirm="deleteFile" />
    </div>
</template>

<script setup>
import { ref, getCurrentInstance, onMounted } from 'vue'

import { Menu, MenuButton, MenuItem, MenuItems } from '@headlessui/vue'
import { EllipsisVerticalIcon } from '@heroicons/vue/20/solid'
import axios from 'axios'
import DeleteDialog from './DeleteDialog.vue'

const files = ref([])
const statuses = {
    associer: 'text-green-700 bg-green-50 ring-green-600/20',
    'In progress': 'text-gray-600 bg-gray-50 ring-gray-500/10',
    Archived: 'text-yellow-800 bg-yellow-50 ring-yellow-600/20',
}
const { proxy } = getCurrentInstance()

const openDialogUpload = ref(false)
const openDialogDelete = ref(false)
const selectedFile = ref(null)
const componentKey = ref(0)

const checkAudioMap = async () => {
    try {
        const response = await axios.get('api/get_audio_files')
        console.log('Fetched audio files:', response.data.audio_files)
        files.value = response.data.audio_files
    } catch (error) {
        console.error('Error getting the list:', error)
    }
}

const showDeleteDialog = (file) => {
    selectedFile.value = file
    openDialogDelete.value = true
}

const deleteFile = async (file) => {
    try {
        await axios.post('/api/remove_file', { audio_file: file.name })
        files.value = files.value.filter(f => f.id !== file.id)
        openDialogDelete.value = false
    } catch (error) {
        console.error('Error deleting file:', error)
    }
}

onMounted(() => {
    checkAudioMap()
    console.log('filesList component mounted')
    proxy.$socketService.on('audio_map_responce', (updatedFiles) => {
        console.log('Received audio_map_responce:')
        files.value = updatedFiles
        checkAudioMap()
    })
    checkAudioMap()

})


</script>
<template>
  <div class="flex flex-none items-center gap-x-4">
    <button @click="handleAssociate"
      class="inline-flex w-full justify-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600">
      Associer un tag
    </button>
    <Menu as="div" class="relative flex-none">
      <MenuButton class="-m-2.5 block p-2.5 text-gray-500 hover:text-gray-900">
        <span class="sr-only">Open options</span>
        <EllipsisVerticalIcon class="h-5 w-5" aria-hidden="true" />
      </MenuButton>
      <MenuItems>
        <MenuItem v-slot="{ active }">
          <button @click="handleDelete"
            :class="[active ? 'bg-gray-50' : '', 'block w-full text-left px-3 py-1 text-sm leading-6 text-gray-900']">
            Delete<span class="sr-only">, {{ file.name }}</span>
          </button>
        </MenuItem>
      </MenuItems>
    </Menu>
  </div>
</template>

<script setup lang="ts">
import { defineProps } from 'vue'
import { Menu, MenuButton, MenuItem, MenuItems } from '@headlessui/vue'
import { EllipsisVerticalIcon } from '@heroicons/vue/20/solid'
import type { LegacyAudioFile } from './types'
import { useFileDialog } from './composables/useFileDialog'

const props = defineProps<{
  file: LegacyAudioFile
}>()

const { openDeleteDialog } = useFileDialog()

const handleDelete = () => {
  openDeleteDialog(props.file)
}

const handleAssociate = () => {
  console.log('Associate clicked for file:', props.file)
}
</script>


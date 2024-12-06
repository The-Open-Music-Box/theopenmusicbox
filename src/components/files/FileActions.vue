<template>
    <div class="flex flex-none items-center gap-x-4">
      <button @click="$emit('associate')"
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
          <MenuItems class="absolute right-0 z-10 mt-2 w-32 origin-top-right rounded-md bg-white py-2 shadow-lg ring-1 ring-gray-900/5 focus:outline-none">
            <MenuItem v-slot="{ active }">
              <button @click="$emit('delete')"
                :class="[active ? 'bg-gray-50' : '', 'block w-full text-left px-3 py-1 text-sm leading-6 text-gray-900']">
                Delete<span class="sr-only">, {{ file.name }}</span>
              </button>
            </MenuItem>
          </MenuItems>
        </transition>
      </Menu>
    </div>
  </template>
  
  <script setup lang="ts">
  import { defineProps, defineEmits } from 'vue'
  import { Menu, MenuButton, MenuItem, MenuItems } from '@headlessui/vue'
  import { EllipsisVerticalIcon } from '@heroicons/vue/20/solid'
  import type { AudioFile } from './FileItem.vue'
  
  defineProps<{
    file: AudioFile
  }>()
  
  defineEmits<{
    (e: 'delete'): void
    (e: 'associate'): void
  }>()
  </script>
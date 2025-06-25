<template>
  <TransitionRoot as="template" :show="open">
    <Dialog as="div" class="relative z-10" @close="$emit('close')">
      <TransitionChild
        as="template"
        enter="ease-out duration-300"
        enter-from="opacity-0"
        enter-to="opacity-100"
        leave="ease-in duration-200"
        leave-from="opacity-100"
        leave-to="opacity-0"
      >
        <div class="fixed inset-0 bg-overlay transition-opacity" />
      </TransitionChild>

      <div class="fixed inset-0 z-10 overflow-y-auto">
        <div class="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
          <TransitionChild
            as="template"
            enter="ease-out duration-300"
            enter-from="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
            enter-to="opacity-100 translate-y-0 sm:scale-100"
            leave="ease-in duration-200"
            leave-from="opacity-100 translate-y-0 sm:scale-100"
            leave-to="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
          >
            <DialogPanel class="relative transform overflow-hidden rounded-lg bg-surface px-4 pb-4 pt-5 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg sm:p-6">
              <div class="sm:flex sm:items-start">
                <div class="mx-auto flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full bg-error-light sm:mx-0 sm:h-10 sm:w-10">
                  <ExclamationTriangleIcon class="h-6 w-6 text-error" aria-hidden="true" />
                </div>
                <div class="mt-3 text-center sm:ml-4 sm:mt-0 sm:text-left">
                  <DialogTitle as="h3" class="text-base font-semibold leading-6 text-onBackground">
                    {{ t('track.delete.title') }}
                  </DialogTitle>
                  <div class="mt-2">
                    <p class="text-sm text-disabled">
                      {{ t('track.delete.confirmation', {
                        title: track?.title || t('track.delete.untitled'),
                        playlist: playlist?.title || t('track.delete.unnamed')
                      }) }}
                    </p>
                  </div>
                </div>
              </div>
              <div class="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse">
                <button
                  type="button"
                  class="inline-flex w-full justify-center rounded-md bg-error px-3 py-2 text-sm font-semibold text-onError shadow-sm hover:bg-error-light sm:ml-3 sm:w-auto"
                  @click="confirmDeletion"
                >
                  {{ t('common.delete') }}
                </button>
                <button
                  type="button"
                  class="mt-3 inline-flex w-full justify-center rounded-md bg-surface px-3 py-2 text-sm font-semibold text-onBackground shadow-sm ring-1 ring-inset ring-border hover:bg-background sm:mt-0 sm:w-auto"
                  @click="$emit('close')"
                  ref="cancelButtonRef"
                >
                  {{ t('common.cancel') }}
                </button>
              </div>
            </DialogPanel>
          </TransitionChild>
        </div>
      </div>
    </Dialog>
  </TransitionRoot>
</template>

<script setup lang="ts">
/**
 * DeleteDialog Component
 *
 * A modal dialog that confirms deletion of a track from a playlist.
 * Provides user with a clear confirmation step before proceeding with deletion.
 */

import { Dialog, DialogPanel, DialogTitle, TransitionChild, TransitionRoot } from '@headlessui/vue'
import { ExclamationTriangleIcon } from '@heroicons/vue/24/outline'
import type { PlayList, Track } from './files/types'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

interface Props {
  /** Whether the dialog is open or closed */
  open: boolean;
  /** The track to be deleted */
  track: Track | null;
  /** The playlist containing the track */
  playlist: PlayList | null;
}

defineProps<Props>()

const emit = defineEmits<{
  /** Emitted when the dialog is closed without confirming */
  (e: 'close'): void;
  /** Emitted when deletion is confirmed */
  (e: 'confirm'): void;
}>()

/**
 * Handles the confirmation of track deletion
 */
const confirmDeletion = () => {
  emit('confirm')
}
</script>
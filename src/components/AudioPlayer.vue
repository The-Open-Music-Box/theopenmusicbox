<template>
  <div class="flex items-center justify-center">
    <div class="w-2/3">
      <div
        class="bg-white border-slate-100 dark:bg-slate-800 dark:border-slate-500 border-b rounded-t-xl p-4 pb-6 sm:p-10 sm:pb-8 lg:p-6 xl:p-10 xl:pb-8 space-y-6 sm:space-y-8 lg:space-y-6 xl:space-y-8 items-center"
      >
        <div class="flex items-center space-x-4">
          <img
            src="https://img.freepik.com/free-psd/square-flyer-template-maximalist-business_23-2148524497.jpg?w=1800&t=st=1699458420~exp=1699459020~hmac=5b00d72d6983d04966cc08ccd0fc1f80ad0d7ba75ec20316660e11efd18133cd"
            alt=""
            width="88"
            height="88"
            class="flex-none rounded-lg bg-slate-100"
            loading="lazy"
          />
          <div class="min-w-0 flex-auto space-y-1 font-semibold">
            <p class="text-cyan-500 dark:text-cyan-400 text-sm leading-6">
              <abbr title="Track">Track:</abbr> 05
            </p>
            <h2
              class="text-slate-500 dark:text-slate-400 text-sm leading-6 truncate"
            >
              Music: New Album The Lorem
            </h2>
            <p class="text-slate-900 dark:text-slate-50 text-lg">Spotisimo</p>
          </div>
        </div>
        <div class="space-y-2">
          <div class="relative">
            <div
              class="bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden"
            >
              <div
                class="bg-cyan-500 dark:bg-cyan-400 h-2"
                :style="{ width: `${progress}%` }"
                role="progressbar"
                aria-label="music progress"
                :aria-valuenow="currentTime"
                :aria-valuemin="0"
                :aria-valuemax="duration"
              ></div>
            </div>
            <div
              class="absolute top-1/2 transform -translate-y-1/2"
              :style="{ left: `${progress}%` }"
            >
              <div
                class="w-4 h-4 flex items-center justify-center bg-white rounded-full shadow"
              >
                <div
                  class="w-1.5 h-1.5 bg-cyan-500 dark:bg-cyan-400 rounded-full ring-1 ring-inset ring-slate-900/5"
                ></div>
              </div>
            </div>
          </div>
          <div
            class="flex justify-between text-sm leading-6 font-medium tabular-nums"
          >
            <div class="text-cyan-500 dark:text-slate-100">
              {{ formatTime(currentTime) }}
            </div>
            <div class="text-slate-500 dark:text-slate-400">
              {{ formatTime(duration) }}
            </div>
          </div>
        </div>
      </div>
      <div
        class="bg-slate-50 text-slate-500 dark:bg-slate-600 dark:text-slate-200 rounded-b-xl flex items-center"
      >
        <div class="flex-auto flex items-center justify-evenly">
          <button
            type="button"
            class="hidden sm:block lg:hidden xl:block"
            aria-label="Previous"
            @click="previous"
          >
            <svg width="24" height="24" fill="none">
              <path
                d="m10 12 8-6v12l-8-6Z"
                fill="currentColor"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
              <path
                d="M6 6v12"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          </button>
          <button type="button" aria-label="Rewind 10 seconds" @click="rewind">
            <svg width="24" height="24" fill="none">
              <path
                d="M6.492 16.95c2.861 2.733 7.5 2.733 10.362 0 2.861-2.734 2.861-7.166 0-9.9-2.862-2.733-7.501-2.733-10.362 0A7.096 7.096 0 0 0 5.5 8.226"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
              <path
                d="M5 5v3.111c0 .491.398.889.889.889H9"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          </button>
        </div>
        <button
          type="button"
          class="bg-white text-slate-900 dark:bg-slate-100 dark:text-slate-700 flex-none -my-2 mx-auto w-20 h-20 rounded-full ring-1 ring-slate-900/5 shadow-md flex items-center justify-center"
          aria-label="Play/Pause"
          @click="togglePlayPause"
        >
          <svg v-if="isPlaying" width="30" height="32" fill="currentColor">
            <rect x="6" y="4" width="4" height="24" rx="2" />
            <rect x="20" y="4" width="4" height="24" rx="2" />
          </svg>
          <svg v-else width="30" height="32" fill="currentColor">
            <polygon points="5,3 25,16 5,29" />
          </svg>
        </button>
        <div class="flex-auto flex items-center justify-evenly">
          <button type="button" aria-label="Skip 10 seconds" @click="skip">
            <svg width="24" height="24" fill="none">
              <path
                d="M17.509 16.95c-2.862 2.733-7.501 2.733-10.363 0-2.861-2.734-2.861-7.166 0-9.9 2.862-2.733 7.501-2.733 10.363 0 .38.365.711.759.991 1.176"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
              <path
                d="M19 5v3.111c0 .491-.398.889-.889.889H15"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          </button>
          <button
            type="button"
            class="hidden sm:block lg:hidden xl:block"
            aria-label="Next"
            @click="next"
          >
            <svg width="24" height="24" fill="none">
              <path
                d="M14 12 6 6v12l8-6Z"
                fill="currentColor"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
              <path
                d="M18 6v12"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
  import { ref, onMounted, onUnmounted } from 'vue'

  const audio = new Audio('')

  const isPlaying = ref(false)

  const currentTime = ref(0)
  const duration = ref(180)
  const progress = ref(0)

  let interval = null

  const updateProgress = () => {
    // currentTime.value = audio.currentTime
    // progress.value = (audio.currentTime / audio.duration) * 100
    if (isPlaying.value) {
      currentTime.value = Math.min(currentTime.value + 0.1, duration.value)
      progress.value = (currentTime.value / duration.value) * 100
      if (currentTime.value >= duration.value) {
        isPlaying.value = false
        clearInterval(interval)
      }
    }
  }

  const togglePlayPause = () => {
    // if (isPlaying.value) {
    //   audio.pause()
    // } else {
    //   audio.play()
    // }
    // isPlaying.value = !isPlaying.value
    if (isPlaying.value) {
      clearInterval(interval)
    } else {
      interval = setInterval(updateProgress, 100) // Update progress every 100ms
    }
    isPlaying.value = !isPlaying.value
  }

  // const rewind = () => {
  //   audio.currentTime = Math.max(0, audio.currentTime - 10)
  // }

  // const skip = () => {
  //   audio.currentTime = Math.min(audio.duration, audio.currentTime + 10)
  // }
  const rewind = () => {
    currentTime.value = Math.max(0, currentTime.value - 10)
    progress.value = (currentTime.value / duration.value) * 100
  }

  const skip = () => {
    currentTime.value = Math.min(duration.value, currentTime.value + 10)
    progress.value = (currentTime.value / duration.value) * 100
  }

  const previous = () => {
    // Implémente ta logique pour le précédent
  }

  const next = () => {
    // Implémente ta logique pour le suivant
  }

  const formatTime = (time) => {
    const minutes = Math.floor(time / 60)
    const seconds = Math.floor(time % 60)
      .toString()
      .padStart(2, '0')
    return `${minutes}:${seconds}`
  }

  // onMounted(() => {
  //   audio.addEventListener('timeupdate', updateProgress)
  //   audio.addEventListener('loadedmetadata', () => {
  //     duration.value = audio.duration
  //   })
  // })

  // onUnmounted(() => {
  //   audio.removeEventListener('timeupdate', updateProgress)
  // })
  onMounted(() => {
    // Initialize the duration and start the interval if playing
    if (isPlaying.value) {
      interval = setInterval(updateProgress, 100)
    }
  })

  onUnmounted(() => {
    if (interval) {
      clearInterval(interval)
    }
  })
</script>

import type { PlayList, Track } from './types'

export const mockTracks: Track[] = [
  {
    number: 1,
    title: "Ocarina of Time",
    filename: "Zelda & Sleep - 001 Ocarina of Time [MTrZXHaXPrU].mp3",
    duration: "180",
    play_counter: 0
  },
  {
    number: 2,
    title: "Zelda's Lullaby",
    filename: "Zelda & Sleep - 002 Zelda's Lullaby [MTrZXHaXPrU].mp3",
    duration: "240",
    play_counter: 0
  },
  {
    number: 3,
    title: "Song of Storms",
    filename: "Zelda & Sleep - 003 Song of Storms [MTrZXHaXPrU].mp3",
    duration: "195",
    play_counter: 0
  }
]

export const mockPlaylists: PlayList[] = [
  {
    id: "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
    type: "playlist",
    idtagnfc: "04A2BEF8780000",
    path: "zelda sleep",
    title: "Zelda & Sleep",
    tracks: mockTracks,
    created_at: "2024-02-12T14:30:00Z",
    last_played: "2024-02-12T15:00:00Z"
  },
  {
    id: "7ba7b810-9dad-11d1-80b4-00c04fd430c9",
    type: "playlist",
    idtagnfc: "04A2BEF8780001",
    path: "relaxation",
    title: "Relaxation & Méditation",
    tracks: [
      {
        number: 1,
        title: "Ocean Waves",
        filename: "Relaxation - 001 Ocean Waves.mp3",
        duration: "300",
        play_counter: 2
      },
      {
        number: 2,
        title: "Forest Ambiance",
        filename: "Relaxation - 002 Forest Ambiance.mp3",
        duration: "360",
        play_counter: 1
      }
    ],
    created_at: "2024-02-12T16:30:00Z",
    last_played: "2024-02-12T17:00:00Z"
  }
] 
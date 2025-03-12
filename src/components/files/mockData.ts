import { AudioFile, FILE_STATUS } from './types'

export const mockFiles: AudioFile[] = [
  {
    id: 1,
    name: "Chanson solo 1.mp3",
    status: FILE_STATUS.IN_PROGRESS,
    duration: 180,
    createdAt: "2024-03-20",
    isAlbum: false
  },
  {
    id: 2,
    name: "Album Rock 2024",
    status: FILE_STATUS.IN_PROGRESS,
    duration: 0,
    createdAt: "2024-03-19",
    isAlbum: true,
    albumFiles: [
      {
        id: 21,
        name: "01 - Introduction.mp3",
        status: FILE_STATUS.IN_PROGRESS,
        duration: 120,
        createdAt: "2024-03-19"
      },
      {
        id: 22,
        name: "02 - Premier morceau.mp3",
        status: FILE_STATUS.IN_PROGRESS,
        duration: 240,
        createdAt: "2024-03-19"
      },
      {
        id: 23,
        name: "03 - Deuxième morceau.mp3",
        status: FILE_STATUS.IN_PROGRESS,
        duration: 180,
        createdAt: "2024-03-19"
      }
    ]
  },
  {
    id: 3,
    name: "Chanson solo 2.mp3",
    status: FILE_STATUS.ASSOCIATED,
    duration: 240,
    createdAt: "2024-03-18",
    isAlbum: false
  },
  {
    id: 4,
    name: "Album Jazz Collection",
    status: FILE_STATUS.IN_PROGRESS,
    duration: 0,
    createdAt: "2024-03-17",
    isAlbum: true,
    albumFiles: [
      {
        id: 41,
        name: "01 - Jazz Standard.mp3",
        status: FILE_STATUS.IN_PROGRESS,
        duration: 360,
        createdAt: "2024-03-17"
      },
      {
        id: 42,
        name: "02 - Improvisation.mp3",
        status: FILE_STATUS.IN_PROGRESS,
        duration: 480,
        createdAt: "2024-03-17"
      }
    ]
  },
  {
    id: 5,
    name: "Chanson solo 3.mp3",
    status: FILE_STATUS.ARCHIVED,
    duration: 200,
    createdAt: "2024-03-16",
    isAlbum: false
  }
] 
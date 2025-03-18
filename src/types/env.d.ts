declare namespace NodeJS {
  interface ProcessEnv {
    NODE_ENV: 'development' | 'production' | 'test'
    VUE_APP_API_URL: string
    VUE_APP_SRV_URL: string
    VUE_APP_USE_MOCK: string
    BASE_URL: string
  }
}

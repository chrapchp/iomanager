/***************************************************
 * Project:     IOManager
 * Author:      Peter Chrapchynski
 * Date:        2026Jun23
 * History:     2026Jun23 - Initial creation
 *              2026Jun24 - Disable component path-prefix so subdirs are organisational only
 *              2026Jul04 - Exclude #app-manifest from optimizeDeps to silence Vite pre-bundle error
 ***************************************************/

import tailwindcss from '@tailwindcss/vite'

export default defineNuxtConfig({
  devtools: { enabled: false },
  css: ['~/assets/css/main.css'],
  modules: ['@pinia/nuxt'],
  components: {
    dirs: [{ path: '~/components', pathPrefix: false }],
  },
  vite: {
    plugins: [tailwindcss()],
    optimizeDeps: {
      exclude: ['#app-manifest'],
    },
  },
  runtimeConfig: {
    public: {
      apiBase: 'http://localhost:8000',
    },
  },
})

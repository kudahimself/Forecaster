import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Env-driven config so the same vite.config works:
//   - native dev (defaults: bind 127.0.0.1, proxy to localhost:8000)
//   - inside Docker (VITE_HOST=0.0.0.0, VITE_API_TARGET=http://backend:8000,
//     VITE_USE_POLLING=1 because Windows bind-mounts don't deliver inotify)
const HOST = process.env.VITE_HOST || '127.0.0.1'
const API_TARGET = process.env.VITE_API_TARGET || 'http://127.0.0.1:8000'
const USE_POLLING = process.env.VITE_USE_POLLING === '1'

export default defineConfig({
  plugins: [react()],
  server: {
    host: HOST,
    port: 5173,
    proxy: {
      '/api': {
        target: API_TARGET,
        changeOrigin: false,
      },
    },
    watch: USE_POLLING ? { usePolling: true, interval: 400 } : undefined,
  },
})

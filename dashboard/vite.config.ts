import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5311,
    proxy: {
      '/api': 'http://localhost:5111',
      '/ws': { target: 'ws://localhost:5111', ws: true },
    },
  },
})

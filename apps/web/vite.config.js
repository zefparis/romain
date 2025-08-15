import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        // Keep the /api prefix so frontend calls like /api/conversations map to backend /api/conversations
      },
      "/chat": {
        target: "http://localhost:8000",
        changeOrigin: true
      }
    }
  }
})

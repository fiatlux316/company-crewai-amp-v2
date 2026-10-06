
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig(() => {
  const target = process.env.API_TARGET || 'http://localhost:8080';
  return {
    plugins: [react()],
    server: {
      proxy: {
        '/api': {
          target: target,
          changeOrigin: true
        },
        '/docs': {
          target: target,
          changeOrigin: true
        },
        '/openapi.json': {
          target: target,
          changeOrigin: true
        }
      }
    }
  }
})

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Запити на /api перенаправляємо на FastAPI (порт 8000), тому CORS у розробці не потрібен
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
})

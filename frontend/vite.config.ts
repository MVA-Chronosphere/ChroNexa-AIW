import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import type { Plugin } from 'vite'

const spaFallback: Plugin = {
  name: 'spa-fallback',
  apply: 'serve',
  configureServer(server) {
    server.middlewares.use((req, res, next) => {
      if (!req.url) return next()
      const url = req.url
      
      // Allow HMR, API, and files through
      if (url.startsWith('/@') || url.startsWith('/api') || url.match(/\.[^/]*$/)) {
        return next()
      }
      
      // Rewrite all other requests to index.html
      req.url = '/index.html'
      next()
    })
  }
}

export default defineConfig({
  appType: 'spa',
  plugins: [spaFallback, react()],
  server: {
    port: 3000,
    middlewareMode: false,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '/api')
      }
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@services': path.resolve(__dirname, './src/services'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@store': path.resolve(__dirname, './src/store'),
      '@types': path.resolve(__dirname, './src/types')
    }
  }
})

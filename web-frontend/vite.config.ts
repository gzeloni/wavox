import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

// In dev, forward API/OAuth/WS calls to the FastAPI backend on :3500
export default defineConfig({
  plugins: [sveltekit()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:3500',
        changeOrigin: true,
        ws: true
      },
      '/dashboard/login': {
        target: 'http://localhost:3500',
        changeOrigin: true
      },
      '/dashboard/callback': {
        target: 'http://localhost:3500',
        changeOrigin: true
      },
      '/dashboard/logout': {
        target: 'http://localhost:3500',
        changeOrigin: true
      }
    }
  }
});

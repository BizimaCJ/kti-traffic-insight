import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// In development the React app runs on :5173 and forwards API calls to Django on :8000,
// so cookies and CSRF behave exactly as in production (same origin).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
      '/django-admin': 'http://localhost:8000',
      '/static': 'http://localhost:8000',
    },
  },
  build: { outDir: 'dist', sourcemap: false },
});

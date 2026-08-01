import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Proxies specific backend paths during dev (npm run dev), so the
// frontend can call e.g. fetch('/triage') directly with no prefix --
// the SAME code path works unchanged when FastAPI serves the built
// frontend directly in single-server mode (see docs/SETUP.md).
const BACKEND_PATHS = ['/triage', '/auth', '/vision-check', '/encounters', '/admin', '/health', '/doctor', '/patient']

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: Object.fromEntries(
      BACKEND_PATHS.map((path) => [
        path,
        { target: 'http://localhost:8000', changeOrigin: true },
      ])
    ),
  },
})

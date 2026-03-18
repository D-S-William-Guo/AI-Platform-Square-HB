import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const frontendDevPort = Number.parseInt(env.FRONTEND_DEV_PORT || '5173', 10)
  const backendDevPort = Number.parseInt(env.BACKEND_DEV_PORT || '8000', 10)
  const appHost = env.APP_HOST || '0.0.0.0'
  const apiBaseUrl = env.VITE_API_BASE_URL || `http://127.0.0.1:${backendDevPort}`

  return {
    plugins: [react()],
    server: {
      host: appHost,
      port: frontendDevPort,
      proxy: {
        '/api': apiBaseUrl,
      },
    },
  }
})

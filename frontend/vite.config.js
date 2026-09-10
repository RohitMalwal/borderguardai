import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

// Local-first dev server. By default we proxy same-origin /api calls to the
// backend on :8000 so the frontend code needs no hard-coded host. The proxy
// target can be overridden with VITE_DEV_PROXY_TARGET (e.g. a LAN IP), and the
// built app can talk to a backend directly via VITE_API_URL (see .env.example).
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const proxyTarget = env.VITE_DEV_PROXY_TARGET || 'http://localhost:8000';

  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        '/api': {
          target: proxyTarget,
          changeOrigin: true,
        },
      },
    },
  };
});

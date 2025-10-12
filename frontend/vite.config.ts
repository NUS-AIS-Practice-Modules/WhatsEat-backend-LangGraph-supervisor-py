import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "VITE_");

  return {
    plugins: [react()],
    server: {
      port: Number(env.VITE_DEV_SERVER_PORT ?? 5173),
      host: true,
      proxy: env.VITE_LANGGRAPH_API_PROXY
        ? {
            "/api": {
              target: env.VITE_LANGGRAPH_API_PROXY,
              changeOrigin: true,
              secure: false,
            },
          }
        : undefined,
    },
    preview: {
      port: Number(env.VITE_PREVIEW_PORT ?? 4173),
    },
  };
});

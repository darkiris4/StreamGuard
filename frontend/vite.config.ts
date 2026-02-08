import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    fs: {
      allow: [".."],
    },
    proxy: {
      "/api": {
        target: "http://backend:8000",
        changeOrigin: true,
        secure: false,
      },
      "/health": {
        target: "http://backend:8000",
        changeOrigin: true,
        secure: false,
      },
      "/ws": {
        target: "ws://backend:8000",
        ws: true,
        changeOrigin: true,
        secure: false,
      },
      "/docs": {
        target: "http://docs:3001",
        changeOrigin: true,
        secure: false,
      },
    },
  },
  assetsInclude: ["**/*.jpg", "**/*.jpeg", "**/*.png"],
});

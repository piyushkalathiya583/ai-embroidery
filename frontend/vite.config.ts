import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// On Vercel the static build is served under /frontend/, so assets must be
// referenced from there in production. Local dev stays at root.
export default defineConfig(({ command }) => ({
  base: command === "build" ? "/frontend/" : "/",
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
      "/files": "http://localhost:8000",
    },
  },
}));

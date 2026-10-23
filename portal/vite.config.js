import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// En desarrollo (npm run dev) /api se redirige a la API local.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": { target: "http://localhost:8000", rewrite: (p) => p.replace(/^\/api/, "") },
    },
  },
});

import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

// The production build goes straight into the backend, which serves it from "/".
export default defineConfig({
  plugins: [react()],
  build: { outDir: "../backend/static", emptyOutDir: true },
  server: { proxy: { "/api": "http://127.0.0.1:8000" } },
  test: { environment: "node" },
});

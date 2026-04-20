import { defineConfig } from "vite";

export default defineConfig({
  base: "/admin/",
  server: {
    proxy: {
      "/api": "http://localhost:8002",
    },
  },
});

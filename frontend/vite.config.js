import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
// Proxy giúp dev gọi cùng /api như bản đã build phục vụ bởi FastAPI.
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, proxy: { "/api": "http://127.0.0.1:8000" } },
});

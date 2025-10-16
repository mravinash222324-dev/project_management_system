import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
export const BASE_URL = "https://project-management-system-1-2cwr.onrender.com";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
})

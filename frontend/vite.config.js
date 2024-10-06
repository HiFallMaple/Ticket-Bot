import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import path from 'path'; // 引入 path 模組

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'), // 設定 '@' 別名指向 'src' 目錄
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000', // 目標伺服器的 URL
        changeOrigin: true, // 改變來源
        // 不進行路徑重寫，將請求直接發送到目標伺服器
      },
      '/ws': {
        target: 'ws://localhost:8000', // 目標伺服器的 URL
        changeOrigin: true, // 改變來源
        ws: true, // 開啟 WebSocket 代理
        // 不進行路徑重寫，將請求直接發送到目標伺服器
      },
    },
  },
});

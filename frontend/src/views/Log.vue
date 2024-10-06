<template>
  <div class="grid max-w-full">
    <div class="lg:col-10 lg:col-offset-1 col-12">
      <div class="flex">
        <h2>實時日誌</h2>
        <Button
          :icon="isLoading ? 'pi pi-spin pi-spinner' : 'pi pi-times'"
          aria-label="關閉腳本"
          class="my-auto ml-auto"
          severity="danger"
          label="關閉腳本"
          @click="stopBot"
        />
      </div>
      <div
        class="logs overflow-y-auto border-solid border-400 border-1 mx-0"
        ref="logContainer"
        style="height: calc(100vh - 250px); white-space: pre-wrap"
      >
        <div class="p-3 pb-1">{{ logs.join("\n") }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import Button from "primevue/button";
import { ref, onMounted, onUnmounted, nextTick } from "vue";
import axios from "axios"; // 引入 axios

const logs = ref([]); // 用來存儲接收到的日誌
const MAX_LOGS = 200; // 日誌的最大條數限制
let websocket = null; // 定義 WebSocket 對象
const logContainer = ref(null); // 用來引用 logs 容器
const reconnectInterval = 3000; // 斷線後重連的時間間隔（3秒）
const isLoading = ref(false); // 新增一個狀態變量來控制圖示

// 建立 WebSocket 連接的函數
const connectWebSocket = () => {
  websocket = new WebSocket("/ws/logs");

  websocket.onopen = () => {
    console.log("WebSocket 連接已建立");
  };

  websocket.onmessage = (event) => {
    // 將新的日誌添加到 logs 並限制總數不超過 200 條
    logs.value.push(event.data);
    if (logs.value.length > MAX_LOGS) {
      logs.value.shift(); // 移除最早的一條日誌
    }
    // 確保 DOM 更新後滾動條移動到底部
    nextTick(() => {
      if (logContainer.value) {
        logContainer.value.scrollTop = logContainer.value.scrollHeight;
      }
    });
  };

  websocket.onclose = () => {
    console.log("WebSocket 連接已關閉，嘗試重新連接...");
    reconnectWebSocket();
  };

  websocket.onerror = (error) => {
    console.error("WebSocket 發生錯誤:", error);
    websocket.close(); // 出現錯誤時關閉連接，並嘗試重連
  };
};

// 嘗試重新連接 WebSocket 的函數
const reconnectWebSocket = () => {
  setTimeout(() => {
    connectWebSocket(); // 重新建立 WebSocket 連接
  }, reconnectInterval);
};

// 停止 Bot 的函數
const stopBot = async () => {
  isLoading.value = true; // 按下按鈕後，將 isLoading 設為 true

  try {
    // 使用 axios 發送 PUT 請求
    await axios.put("/api/bot/tixcraft", { action: "stop" });
    console.log("腳本已停止");
  } catch (error) {
    console.error("停止腳本時發生錯誤:", error);
  } finally {
    isLoading.value = false; // 不論請求成功或失敗，最終都將 isLoading 設為 false
  }
};

// 當組件掛載時，建立 WebSocket 連接
onMounted(() => {
  connectWebSocket();
});

// 當組件卸載時，關閉 WebSocket 連接
onUnmounted(() => {
  if (websocket) {
    websocket.close();
  }
});
</script>

<style scoped></style>

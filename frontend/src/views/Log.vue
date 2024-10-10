<template>
  <ConfirmDialog group="headless">
    <template #container="{ message, acceptCallback, rejectCallback }">
      <div class="p-3 px-6 bg-surface-0 dark:bg-surface-900 rounded">
        <p class="mb-0 text-lg mt-4">{{ message.message }}</p>
        <div class="flex items-center justify-content-center pt-4 pb-0">
          <Button
            :label="message.acceptProps.label"
            @click="acceptCallback"
            class="w-32"
          ></Button>
        </div>
      </div>
    </template>
  </ConfirmDialog>

  <div class="grid max-w-full">
    <div class="lg:col-10 lg:col-offset-1 col-12">
      <div class="flex">
        <h2>實時日誌</h2>
        <div class="ml-auto flex">
          <Button
            v-if="status !== 'stopped'"
            :label="status === 'running' ? '暫停腳本' : '繼續腳本'"
            :icon="status === 'running' ? 'pi pi-pause' : 'pi pi-step-forward'"
            class="my-auto"
            severity="info"
            @click="handleToggle"
            :disabled="isLoading"
          />
          <Button
            v-if="status !== 'stopped'"
            :icon="isLoading ? 'pi pi-spin pi-spinner' : 'pi pi-times'"
            aria-label="強制關閉"
            class="my-auto ml-2"
            severity="danger"
            label="強制關閉"
            @click="stopBot"
            :disabled="isLoading"
          />
          <Button
            v-if="status === 'stopped'"
            icon="pi pi-home"
            aria-label="回到首頁"
            class="my-auto ml-2 no-underline"
            label="回到首頁"
            as="router-link"
            to="/"
            :disabled="isLoading"
          />
        </div>
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
import { useConfirm } from "primevue/useconfirm";
import ConfirmDialog from "primevue/confirmdialog";

const confirm = useConfirm();
const logs = ref([]); // 用來存儲接收到的日誌
const MAX_LOGS = 200; // 日誌的最大條數限制
const logContainer = ref(null); // 用來引用 logs 容器
const reconnectInterval = 3000; // 斷線後重連的時間間隔（3秒）
const isLoading = ref(false); // 控制圖示
const status = ref("stopped"); // 用來存儲腳本狀態
let logWebSocket = null; // 定義 log WebSocket 對象
let statusWebSocket = null; // 定義 status WebSocket 對象

// handleToggle 定義
const handleToggle = async () => {
  isLoading.value = true;
  let action = status.value === "running" ? "pause" : "continue";
  try {
    await axios.put("/api/bot/tixcraft", { action: action });
  } catch (error) {
    console.error("切換腳本狀態時發生錯誤:", error);
  } finally {
    isLoading.value = false;
  }
};

// 公共的 WebSocket 連接邏輯，接收 URL 和事件回調
const connectWebSocket = (url, onMessageCallback) => {
  const websocket = new WebSocket(url);

  websocket.onopen = () => {
    console.log(`${url} WebSocket 連接已建立`);
  };

  websocket.onmessage = (event) => {
    onMessageCallback(event.data);
  };

  websocket.onclose = () => {
    console.log(`${url} WebSocket 連接已關閉，嘗試重新連接...`);
    reconnectWebSocket(url, onMessageCallback);
  };

  websocket.onerror = (error) => {
    console.error(`${url} WebSocket 發生錯誤:`, error);
    websocket.close();
  };

  return websocket;
};

// 用於重新連接 WebSocket 的函數
const reconnectWebSocket = (url, onMessageCallback) => {
  setTimeout(() => {
    if (url.includes("logs")) {
      logWebSocket = connectWebSocket(url, onMessageCallback);
    } else if (url.includes("status")) {
      statusWebSocket = connectWebSocket(url, onMessageCallback);
    }
  }, reconnectInterval);
};

// log WebSocket 的回調
const handleLogMessage = (message) => {
  if (message.includes("WARNING - confirm_login")) {
    confirmLogin();
  } else {
    logs.value.push(message);
    if (logs.value.length > MAX_LOGS) {
      logs.value.shift();
    }
    nextTick(() => {
      if (logContainer.value) {
        logContainer.value.scrollTop = logContainer.value.scrollHeight;
      }
    });
  }
};

// status WebSocket 的回調
const handleStatusMessage = (message) => {
  status.value = message;
  console.log("狀態更新為:", status.value);
  // 可以根據需求處理狀態訊息
};

// 確認登入的對話框邏輯
const confirmLogin = () => {
  confirm.require({
    group: "headless",
    message: "請登入後再按下確認繼續腳本",
    header: "登入",
    icon: "pi pi-exclamation-triangle",
    acceptProps: {
      label: "繼續",
    },
    accept: () => {
      continueBot();
    },
  });
};

// 繼續 Bot
const continueBot = async () => {
  try {
    const response = await axios.put("/api/bot/tixcraft", {
      action: "continue",
    });
    console.log("腳本已繼續", response.data);
  } catch (error) {
    console.error("繼續腳本時發生錯誤:", error);
  }
};

// 停止 Bot 的函數
const stopBot = async () => {
  isLoading.value = true;
  try {
    await axios.put("/api/bot/tixcraft", { action: "stop" });
    console.log("腳本已停止");
    await fetchStatus(); // 獲取當前狀態
  } catch (error) {
    console.error("停止腳本時發生錯誤:", error);
  } finally {
    isLoading.value = false;
  }
};

// 新增函數來獲取當前狀態
const fetchStatus = async () => {
  try {
    const response = await axios.get("/api/bot/tixcraft");
    status.value = response.data.status; // 更新狀態
  } catch (error) {
    console.error("獲取狀態時發生錯誤:", error);
  }
};

// 當組件掛載時，建立 WebSocket 連接並獲取狀態
onMounted(() => {
  logWebSocket = connectWebSocket("/ws/logs", handleLogMessage); // 連接 log WebSocket
  statusWebSocket = connectWebSocket("/ws/thread/status", handleStatusMessage); // 連接 status WebSocket
  fetchStatus(); // 獲取當前狀態
});

// 當組件卸載時，關閉所有 WebSocket 連接
onUnmounted(() => {
  if (logWebSocket) {
    logWebSocket.close();
  }
  if (statusWebSocket) {
    statusWebSocket.close();
  }
});
</script>

<style scoped></style>

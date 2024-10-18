<template>
  <div class="card flex justify-center">
    <Dialog v-model:visible="visible" :position="position">
      <template #container="{ closeCallback }">
        <div class="p-3 pt-4 px-4">
          <p class="text-center w-full m-0">機器人正在後台運行</p>
          <div class="flex justify-content-center gap-2 mt-3">
            <Button
              label="查看"
              class="my-auto ml-2 no-underline"
              as="router-link"
              to="/log"
            />
            <Button
              type="button"
              severity="danger"
              label="關閉"
              @click="visible = false"
              :disabled="isLoading"
            ></Button>
          </div>
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, h } from "vue";
import Dialog from "primevue/dialog";
import Button from "primevue/button";

const visible = ref(false);
const isLoading = ref(false);
const status = ref("stopped");
const position = ref("bottomright");
let websocket = null; // WebSocket 連接對象


const connectWebSocket = () => {
  websocket = new WebSocket("ws://localhost:8000/ws/thread/status"); // 連接到你的 WebSocket 路徑

  // 當連線建立時
  websocket.onopen = () => {
    console.log("WebSocket 已連接");
  };

  // 當收到 WebSocket 訊息時
  websocket.onmessage = (event) => {
    console.log("status:", event.data);
    status.value = event.data;
    if (event.data !== "stopped") {
      visible.value = true;
    }
  };

  // 當 WebSocket 關閉時
  websocket.onclose = () => {
    console.log("WebSocket 已關閉");
  };

  // 當 WebSocket 發生錯誤時
  websocket.onerror = (error) => {
    console.error("WebSocket 錯誤:", error);
  };
};

onMounted(() => {
  connectWebSocket(); // 當組件掛載時建立 WebSocket 連接
});

onUnmounted(() => {
  if (websocket) {
    websocket.close(); // 當組件卸載時關閉 WebSocket 連接
  }
});
</script>

<style scoped></style>

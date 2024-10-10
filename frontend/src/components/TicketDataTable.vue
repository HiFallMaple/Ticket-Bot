<template>
  <DataTable
    v-model:selection="selectedSession"
    :value="sessions"
    dataKey="id"
    tableStyle="min-width: 50rem"
    class="mb-4"
  >
    <template #header>
      <div class="flex">
        <div class="flex flex-wrap align-items-center gap-2">
          <h3 class="-ml-2 my-0">欲搶購場次</h3>
        </div>
        <Button
          :icon="loading ? 'pi pi-spin pi-spinner' : 'pi pi-refresh'"
          aria-label="Refresh"
          @click="refreshData"
          class="ml-auto"
          text
          :disabled="loading"
        />
      </div>
    </template>

    <Column selectionMode="multiple" headerStyle="width: 3rem"></Column>
    <Column field="performance_time" header="Performance Time"></Column>
    <Column field="event_name" header="Event Name"></Column>
    <Column field="venue" header="Venue"></Column>
    <template #footer>
      <div class="flex flex-wrap items-center justify-between gap-2">
        <span>
          {{
            sessions.length === 0
              ? "目前無場次資訊"
              : "已選擇 " + selectedIndex.length + " 場次"
          }}
        </span>
      </div>
    </template>
  </DataTable>
</template>

<script setup>
import { ref, onMounted, watch } from "vue";
import DataTable from "primevue/datatable";
import Column from "primevue/column";
import Button from "primevue/button";
import axios from "axios";

// 定義變數
const sessions = ref([]);
const selectedSession = ref([]);
const selectedIndex = defineModel("selectedIndex");
const loading = ref(false); // 新增 loading 狀態
const props = defineProps({
  eventURL: {
    type: String,
    required: false,
  },
});

// 刷新數據的函數
const refreshData = async () => {
  loading.value = true; // 開始加載，設置 loading 為 true
  sessions.value = []; // 清空 sessions

  // 使用 props.eventURL 來獲取傳入的 eventURL
  const eventUrl = props.eventURL;
  console.log("Refreshing data with eventURL:", eventUrl);
  try {
    // 發送 GET 請求，並根據判斷設置查詢參數 url
    const response = await axios.get("/api/event/tixcraft", {
      params: {
        event_url: eventUrl ? eventUrl : null, // 如果 eventURL 存在，傳遞，否則傳 null
      },
    });
    sessions.value = response.data;
  } catch (error) {
    console.error("Error fetching config:", error);
  } finally {
    loading.value = false; // 完成後設置 loading 為 false
  }
};

// 在組件加載時調用 refreshData 函數
onMounted(async () => {
  await refreshData();
  // 監視 selectedIndex 的變化
  watch(selectedIndex, (newSelectedIndex) => {
    console.log("selectedIndex changed:", newSelectedIndex);
    const newSelectedSessions = newSelectedIndex
      .map((id) => sessions.value.find((session) => session.id === id))
      .filter(Boolean); // 過濾掉 undefined 的項目

    // 只有當 selectedSession 發生變化時，才更新
    if (
      JSON.stringify(newSelectedSessions) !==
      JSON.stringify(selectedSession.value)
    ) {
      selectedSession.value = newSelectedSessions;
    }
  });

  // 當 selectedSession 更新時，自動更新 selectedIndex
  watch(selectedSession, (newSelectedSession) => {
    const newSelectedIndex = newSelectedSession.map((session) => session.id);
    console.log("selectedSession changed:", newSelectedSession);
    console.log("session", sessions.value);
    // 只有當 selectedIndex 發生變化時，才更新
    if (
      JSON.stringify(newSelectedIndex) !== JSON.stringify(selectedIndex.value)
    ) {
      selectedIndex.value = newSelectedIndex;
    }
  });
});
</script>

<style scoped></style>

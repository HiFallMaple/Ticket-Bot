<template>
  <DataTable
    v-model:selection="selectedSession"
    :value="sessions"
    :reorderableColumns="true"
    @rowReorder="onRowReorder"
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
    <Column rowReorder headerStyle="width: 3rem" :reorderableColumn="false" />
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
const lock = ref(false);
const props = defineProps({
  eventURL: {
    type: String,
    required: false,
  },
});

const onRowReorder = (event) => {
  if (lock.value) return;
  sessions.value = event.value;
  updateSelectedIndex(sessions.value, selectedSession.value);
  console.log("Selected session IDs in new order:", selectedIndex);
};

const updateSelectedIndex = (_sessions, _selectedSession) => {
  lock.value = true;
  console.log("updateSelectedIndex");
  console.log("_sessions", _sessions);
  console.log("_selectedSession", _selectedSession);
  selectedIndex.value.length = 0;
  for (const session of _sessions) {
    if (_selectedSession.includes(session)) {
      selectedIndex.value.push(session.id);
    }
  }
  console.log("selectedIndex", selectedIndex.value);
  console.log("updateSelectedIndex end");
  lock.value = false;
};

const updateSelectedSession = () => {
  // 根據 selectedSessionIndex 的順序，從 sessions 中找出對應的 session
  lock.value = true;
  console.log("updateSelectedSession");
  console.log("selectedIndex", selectedIndex.value);
  const tmpSessions = [...sessions.value];
  sessions.value.length = 0;
  selectedSession.value.length = 0;
  for (const index of selectedIndex.value) {
    const session = tmpSessions.find((s) => s.id === index);
    if (session) {
      sessions.value.push(session);
    }
  }
  selectedSession.value = selectedIndex.value
    .map((index) => tmpSessions.find((s) => s.id === index))
    .filter(Boolean);
  // 把剩下沒有push進去的session加進去
  for (const session of tmpSessions) {
    if (!selectedSession.value.includes(session)) {
      sessions.value.push(session);
    }
  }
  console.log("selectedSession", selectedSession.value);
  console.log("sessions", sessions.value);
  console.log("updateSelectedSession end");
  lock.value = false;
};

watch(selectedSession, (newVal) => {
  if (lock.value) return;
  console.log("selectedSession changed", newVal);
  console.log("lock", lock.value);
  updateSelectedIndex(sessions.value, newVal);
});

watch(selectedIndex, (newVal) => {
  if (lock.value) return;
  console.log("selectedIndex changed", newVal);
  console.log("lock", lock.value);
  updateSelectedSession();
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
    updateSelectedSession();
  }
};

// 在組件加載時調用 refreshData 函數
onMounted(async () => {
  await refreshData();
});
</script>

<style scoped></style>

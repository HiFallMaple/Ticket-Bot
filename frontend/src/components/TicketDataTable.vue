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
        <span>已選擇 {{ selectedIndex.length }} 場次</span>
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


watch(selectedIndex, (newSelectedIndex) => {
  const newSelectedSessions = newSelectedIndex
    .map((id) => sessions.value.find((session) => session.id === id))
    .filter(Boolean); // 過濾掉 undefined 的項目

  // 只有當 selectedSession 發生變化時，才更新
  if (JSON.stringify(newSelectedSessions) !== JSON.stringify(selectedSession.value)) {
    selectedSession.value = newSelectedSessions;
  }
});

// 當 selectedSession 更新時，自動更新 selectedIndex
watch(selectedSession, (newSelectedSession) => {
  const newSelectedIndex = newSelectedSession.map((session) => session.id);
  
  // 只有當 selectedIndex 發生變化時，才更新
  if (JSON.stringify(newSelectedIndex) !== JSON.stringify(selectedIndex.value)) {
    selectedIndex.value = newSelectedIndex;
  }
});

const refreshData = async () => {
  loading.value = true; // 開始加載，設置 loading 為 true
  sessions.value = []; // 清空 products
  try {
    const response = await axios.get("/api/event/tixcraft");
    sessions.value = response.data;
  } catch (error) {
    console.error("Error fetching config:", error);
  } finally {
    loading.value = false; // 完成後設置 loading 為 false
  }
};

onMounted(async () => {
  await refreshData();
});
</script>

<style scoped></style>

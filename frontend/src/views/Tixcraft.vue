<script setup>
import TicketDataTable from "@/components/TicketDataTable.vue";
import LabelInputText from "@/components/LabelInputText.vue";
import LabelToggleSwitch from "@/components/LabelToggleSwitch.vue"; // 引入新組件
import InputNumber from "primevue/inputnumber";
import Divider from "primevue/divider";
import Button from "primevue/button";
import DatePicker from "primevue/datepicker";
import { useToast } from "primevue/usetoast";
import { useConfirm } from "primevue/useconfirm";
import axios from "axios"; // 引入 axios
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router"; // 引入 vue-router 用來跳轉頁面
import Toast from "primevue/toast";
import ConfirmDialog from "primevue/confirmdialog";

const confirm = useConfirm();
const toast = useToast();
const router = useRouter(); // 使用 vue-router 跳轉

const REQUEST_TICKETS = ref(null);
const TIXCRAFT_SESSION_INDEX_LIST = ref([]); // 用於記錄選中的項目
const KEYWORD_LIST = ref(""); // 記錄輸入的關鍵字
const TIXCRAFT_EVENT_URL = ref(null);
const TARGET_TIME_STR = ref(null);
const AUTO_LOGIN = ref(false);
const AUTO_INPUT_CAPTCHA = ref(false);

const keyword_list_str = ref(null);
const target_time = ref(null);
const target_time_s = ref(null);
const target_time_ms = ref(null);
const isPurchasing = ref(false); // 狀態控制變數，用於切換按鈕的狀態

const startPurchase = async () => {
  isPurchasing.value = true; // 設定為進行中，改變按鈕狀態

  // 阻塞呼叫 saveData，確保保存配置成功
  try {
    await saveData();
    console.log("Config saved successfully.");
  } catch (error) {
    console.error("Failed to save config:", error);
    isPurchasing.value = false; // 若出錯，恢復按鈕狀態
    return;
  }

  // 發送請求到 /api/bot/tixcraft，並阻塞等待回應
  try {
    const response = await axios.put("/api/bot/tixcraft", { action: "run" });
    if (response.status === 200) {
      console.log("Ticket purchase started.");
      // 搶票成功，跳轉至 /log
      router.push("/log");
    } else {
      console.error("Failed to start ticket purchase:", response);
    }
  } catch (error) {
    console.error("Error starting ticket purchase:", error);
  }

  isPurchasing.value = false; // 無論成功與否，最終恢復按鈕狀態
};

const saveData = async () => {
  TARGET_TIME_STR.value = (() => {
    const year = target_time.value.getFullYear();
    const month = String(target_time.value.getMonth() + 1).padStart(2, "0"); // 月份從0開始，所以要加1
    const day = String(target_time.value.getDate()).padStart(2, "0");
    const hours = String(target_time.value.getHours()).padStart(2, "0");
    const minutes = String(target_time.value.getMinutes()).padStart(2, "0");
    return `${year}/${month}/${day} ${hours}:${minutes}:${target_time_s.value}.${target_time_ms.value}`;
  })();
  KEYWORD_LIST.value = keyword_list_str.value.split(",");

  if (
    !REQUEST_TICKETS.value ||
    !KEYWORD_LIST.value ||
    !TIXCRAFT_EVENT_URL.value ||
    !TARGET_TIME_STR.value
  ) {
    console.log("Please make sure all fields are filled in.");
    toast.add({
      severity: "error",
      summary: "Error",
      detail: "請確定所有欄位已填寫",
      life: 3000,
    });
    return;
  }

  if (
    !TIXCRAFT_SESSION_INDEX_LIST.value ||
    TIXCRAFT_SESSION_INDEX_LIST.value.length === 0
  ) {
    console.log("TIXCRAFT_SESSION_INDEX_LIST.value", TIXCRAFT_SESSION_INDEX_LIST.value);
    toast.add({
      severity: "error",
      summary: "Error",
      detail: "請選擇至少一個場次",
      life: 3000,
    });
    return;
  }
  const config = {
    REQUEST_TICKETS: REQUEST_TICKETS.value,
    TIXCRAFT_SESSION_INDEX_LIST: TIXCRAFT_SESSION_INDEX_LIST.value,
    KEYWORD_LIST: KEYWORD_LIST.value,
    AUTO_LOGIN: AUTO_LOGIN.value,
    TIXCRAFT_EVENT_URL: TIXCRAFT_EVENT_URL.value,
    TARGET_TIME_STR: TARGET_TIME_STR.value,
    AUTO_INPUT_CAPTCHA: AUTO_INPUT_CAPTCHA.value,
  };
  try {
    const response = await axios.put("/api/config", config);
    toast.add({
      severity: "success",
      summary: "成功",
      detail: "成功保存配置",
      life: 3000,
    });
    console.log("Config updated successfully:", response.data);
  } catch (error) {
    console.error("Error updating config:", error);
    throw error;
  }
};

onMounted(async () => {
  try {
    const response = await axios.get("/api/config");
    const config = response.data;
    REQUEST_TICKETS.value = config.REQUEST_TICKETS;
    TIXCRAFT_SESSION_INDEX_LIST.value = config.TIXCRAFT_SESSION_INDEX_LIST;
    console.log("___TIXCRAFT_SESSION_INDEX_LIST", TIXCRAFT_SESSION_INDEX_LIST.value);
    TIXCRAFT_EVENT_URL.value = config.TIXCRAFT_EVENT_URL;
    TARGET_TIME_STR.value = config.TARGET_TIME_STR;
    AUTO_LOGIN.value = config.AUTO_LOGIN;
    AUTO_INPUT_CAPTCHA.value = config.AUTO_INPUT_CAPTCHA;

    keyword_list_str.value = config.KEYWORD_LIST.join(",");
    target_time.value = new Date(config.TARGET_TIME_STR.substring(0, 16));
    target_time_s.value = parseInt(
      config.TARGET_TIME_STR.substring(17, 19),
      10
    );
    target_time_ms.value = parseInt(config.TARGET_TIME_STR.split(".")[1], 10);
  } catch (error) {
    console.error("Error fetching config:", error);
  }
});

const comfirmToStart = () => {
  confirm.require({
    group: "headless",
    message: "要開始搶票嗎？",
    header: " ",
    icon: "pi pi-exclamation-triangle",
    rejectProps: {
      label: "取消",
      severity: "secondary",
      outlined: true,
    },
    acceptProps: {
      label: "開始",
    },
    accept: () => {
      startPurchase();
    },
    reject: () => {
    },
  });
};
</script>

<template>
  <Toast />
  <ConfirmDialog group="headless">
    <template #container="{ message, acceptCallback, rejectCallback }">
      <div class="p-3 px-6 bg-surface-0 dark:bg-surface-900 rounded">
        <p class="mb-0 text-lg text-center mt-4">{{ message.message }}</p>
        <div class="flex items-center justify-content-center pt-4 pb-0">
          <Button
            :label="message.rejectProps.label"
            @click="rejectCallback"
            class="w-32 mr-2"
            severity="secondary"
          ></Button>
          <Button
            :label="message.acceptProps.label"
            @click="acceptCallback"
            class="w-32"
          ></Button>
        </div>
      </div>
    </template>
  </ConfirmDialog>

  <div class="grid max-w-full mt-2 mb-4">
    <div class="col-12 lg:col-10 lg:col-offset-1 lg:px-0 px-4">
      <div class="flex justify-content-between align-content-center">
        <h1>拓元</h1>
        <div class="flex">
          <Button
            aria-label="Save"
            label="保存"
            class="my-auto"
            severity="secondary"
            @click="saveData"
            :disabled="isPurchasing"
          />
          <Button
            aria-label="Start Purchase"
            label="開始搶票"
            :icon="
              isPurchasing
                ? 'pi pi-spin pi-spinner'
                : 'pi pi-arrow-circle-right'
            "
            class="my-auto ml-2"
            @click="comfirmToStart"
            :disabled="isPurchasing"
          />
        </div>
      </div>
      <Divider />
      <LabelToggleSwitch
        v-model="AUTO_LOGIN"
        label="自動登入"
        helpText="使用 Google 第一個帳號"
      />
      <LabelToggleSwitch
        v-model="AUTO_INPUT_CAPTCHA"
        label="自動輸入驗證碼"
        helpText="使用 ddddocr 辨識，可能有錯誤"
      />
      <div class="grid">
        <div class="grid grid-nogutter col-6">
          <h3 class="col-12">搶購時間</h3>
          <div class="col-6">
            <DatePicker
              id="datepicker-24h"
              v-model="target_time"
              showTime
              hourFormat="24"
              fluid
              dateFormat="yy/mm/dd"
            />
          </div>
          <div class="col-3">
            <InputNumber
              v-model="target_time_s"
              inputId="target_time_s"
              showButtons
              mode="decimal"
              :min="0"
              :max="59"
              placeholder="s"
              fluid
            />
          </div>
          <div class="col-3">
            <InputNumber
              v-model="target_time_ms"
              inputId="target_time_ms"
              showButtons
              mode="decimal"
              :min="0"
              :max="999"
              placeholder="ms"
              fluid
            />
          </div>
        </div>
        <div class="col-6"></div>
        <div class="col-3">
          <h3>搶購數量</h3>
          <InputNumber
            v-model="REQUEST_TICKETS"
            inputId="request_tickets"
            showButtons
            mode="decimal"
            :min="0"
            :max="100"
            fluid
          />
        </div>
        <LabelInputText
          v-model="keyword_list_str"
          label="搶購的關鍵字"
          placeholder="1F,3080,5505"
          inputId="keywords_list"
          class="col-3"
        />
        <div class="col-6"></div>
        <LabelInputText
          v-model="TIXCRAFT_EVENT_URL"
          label="購票網址"
          placeholder="https://tixcraft.com/activity/game/25_mogwaitp"
          inputId="event-url"
          class="col-6"
          helpText="請將網址中 detail 改為 game"
        />
      </div>
      <TicketDataTable
        class="-mx-2 my-2"
        :eventURL=TIXCRAFT_EVENT_URL
        v-model:selectedIndex="TIXCRAFT_SESSION_INDEX_LIST"
      />
    </div>
  </div>
</template>

<style scoped></style>

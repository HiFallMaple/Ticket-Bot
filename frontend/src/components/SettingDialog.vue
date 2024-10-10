<template>
  <Dialog
    v-model:visible="visible"
    maximizable
    modal
    :style="{ width: '50rem' }"
    :breakpoints="{ '1199px': '75vw', '575px': '90vw' }"
  >
    <template #header>
      <h1 class="my-0">設定</h1>
    </template>
    <div class="p-1">
      <LabelToggleSwitch
        v-model="TRY_AGAIN_WHEN_ERROR"
        label="自動重啟腳本"
        helpText="當腳本發生錯誤時，將重啟腳本重新搶票"
      />
      <LabelInputText
        v-model="CHROME_PROFILE_DIR_PATH"
        label="Chrome Profile 目錄"
        placeholder="Default"
        inputId="chrome_profile_dir"
      />
      <LabelInputText
        v-model="NOTIFY_PREFIX"
        label="通知前綴"
        placeholder="Tony"
        inputId="notify_prefix"
      />
      <LabelInputText
        v-model="SUCCESS_MESSAGE"
        label="搶票成功訊息"
        placeholder="已成功購票，請盡速付款"
        inputId="sucess_message"
      />
      <LabelInputText
        v-model="TG_TOKEN"
        label="Telegram token"
        placeholder="XXXXXXXXX:XXXXXXXX"
        inputId="tg_token"
      />
      <LabelInputText
        v-model="TG_CHAT_ID"
        label="Telegram chat ID"
        placeholder="XXXXXXXXX"
        inputId="tg_chat_id"
      />
      <LabelInputText
        v-model="LINE_NOTIFY_TOKEN"
        label="Line notify token"
        placeholder="XXXXXXXXX"
        inputId="line_notify_token"
        class="mb-4"
      />
    </div>
    <template #footer>
      <Button label="保存" @click="updateSetting" />
    </template>
  </Dialog>
</template>

<script setup>
import { ref, watch } from "vue";
import Button from "primevue/button";
import axios from "axios";
import Dialog from "primevue/dialog";
import LabelInputText from "@/components/LabelInputText.vue";
import LabelToggleSwitch from "@/components/LabelToggleSwitch.vue";

// 定義變數
const visible = defineModel("visible");
const CHROME_PROFILE_DIR_PATH = ref(null);
const NOTIFY_PREFIX = ref(null);
const SUCCESS_MESSAGE = ref(null);
const TG_TOKEN = ref(null);
const TG_CHAT_ID = ref(null);
const LINE_NOTIFY_TOKEN = ref(null);
const TRY_AGAIN_WHEN_ERROR = ref(false);

// 定義獲取設置的函數
const getSettings = async () => {
  try {
    const response = await axios.get("/api/config");
    const config = response.data;

    // 將 API 返回的數據賦值給對應的變數
    CHROME_PROFILE_DIR_PATH.value = config.CHROME_PROFILE_DIR_PATH;
    NOTIFY_PREFIX.value = config.NOTIFY_PREFIX;
    SUCCESS_MESSAGE.value = config.SUCCESS_MESSAGE;
    TG_TOKEN.value = config.TG_TOKEN;
    TG_CHAT_ID.value = config.TG_CHAT_ID;
    LINE_NOTIFY_TOKEN.value = config.LINE_NOTIFY_TOKEN;
    TRY_AGAIN_WHEN_ERROR.value = config.TRY_AGAIN_WHEN_ERROR; // 假設這個屬性在 API 返回中

    console.log("API Config Response:", config); // 印出 API 返回的數據
  } catch (error) {
    console.error("Error fetching config:", error);
  }
};

// 當對話框隱藏時記錄設置
const updateSetting = async () => {
  const settings = {
    CHROME_PROFILE_DIR_PATH: CHROME_PROFILE_DIR_PATH.value,
    NOTIFY_PREFIX: NOTIFY_PREFIX.value,
    SUCCESS_MESSAGE: SUCCESS_MESSAGE.value,
    TG_TOKEN: TG_TOKEN.value,
    TG_CHAT_ID: TG_CHAT_ID.value,
    LINE_NOTIFY_TOKEN: LINE_NOTIFY_TOKEN.value,
    TRY_AGAIN_WHEN_ERROR: TRY_AGAIN_WHEN_ERROR.value,
  };
  console.log("Settings to update:", settings);

  try {
    const response = await axios.put("/api/config", settings);
    console.log("Settings updated successfully:", response.data);
    setting_visible.value = false; // 關閉對話框
  } catch (error) {
    console.error("Error updating settings:", error);
  }
};

watch(visible, (newValue) => {
  if (newValue === true) {
    getSettings();
  }
});
</script>

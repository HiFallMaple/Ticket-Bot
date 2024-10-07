<template>
  <Menubar :model="items">
    <!-- 左側的圖標和標題 -->
    <template #start>
      <a href="/" class="flex no-underline align-content-center">
        <img class="h-2rem" alt="FallMaple" src="@/assets/maple-leaf.png" />
        <span class="title mr-3 mt-1">FallMaple</span>
      </a>
    </template>

    <template #item="{ item, props, hasSubmenu }">
      <router-link
        v-if="item.route"
        v-slot="{ href, navigate }"
        :to="item.route"
        custom
      >
        <a v-ripple :href="href" v-bind="props.action" @click="navigate">
          <span :class="item.icon" />
          <span class="ml-2">{{ item.label }}</span>
        </a>
      </router-link>
      <a
        v-else
        v-ripple
        :href="item.url"
        :target="item.target"
        v-bind="props.action"
      >
        <span :class="item.icon" />
        <span class="ml-2">{{ item.label }}</span>
        <span v-if="hasSubmenu" class="pi pi-fw pi-angle-down ml-2" />
      </a>
    </template>

    <!-- 右側的設定按鈕 -->
    <template #end>
      <Button
        icon="pi pi-cog"
        aria-label="Settings"
        severity="secondary"
        text
        @click="getSettings"
      />
    </template>
  </Menubar>

  <Dialog
    v-model:visible="setting_visible"
    maximizable
    modal
    :style="{ width: '50rem' }"
    :breakpoints="{ '1199px': '75vw', '575px': '90vw' }"
  >
    <template #header>
      <h1 class="my-0">設定</h1>
    </template>
    <div class="p-1">
      <div class="flex flex-column">
        <h3>自動重啟腳本</h3>
        <small class="-mt-2 mb-2">當腳本發生錯誤時，將重啟腳本重新搶票</small>
        <ToggleSwitch v-model="TRY_AGAIN_WHEN_ERROR" />
      </div>
      <Label_InputText
        v-model="CHROME_PROFILE_DIR_PATH"
        label="Chrome Profile 目錄"
        placeholder="Default"
        inputId="chrome_profile_dir"
      />
      <Label_InputText
        v-model="NOTIFY_PREFIX"
        label="通知前綴"
        placeholder="Tony"
        inputId="notify_prefix"
      />
      <Label_InputText
        v-model="SUCCESS_MESSAGE"
        label="搶票成功訊息"
        placeholder="已成功購票，請盡速付款"
        inputId="sucess_message"
      />
      <Label_InputText
        v-model="TG_TOKEN"
        label="Telegram token"
        placeholder="XXXXXXXXX:XXXXXXXX"
        inputId="tg_token"
      />
      <Label_InputText
        v-model="TG_CHAT_ID"
        label="Telegram chat ID"
        placeholder="XXXXXXXXX"
        inputId="tg_chat_id"
      />
      <Label_InputText
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
import { ref } from "vue"; 
import Menubar from "primevue/menubar";
import Button from "primevue/button";
import Dialog from "primevue/dialog";
import Label_InputText from "@/components/Label_InputText.vue";
import ToggleSwitch from "primevue/toggleswitch";
import axios from "axios"; // 引入 axios

const setting_visible = ref(false);

const CHROME_PROFILE_DIR_PATH = ref(null);
const NOTIFY_PREFIX = ref(null);
const SUCCESS_MESSAGE = ref(null);
const TG_TOKEN = ref(null);
const TG_CHAT_ID = ref(null);
const LINE_NOTIFY_TOKEN = ref(null);
const TRY_AGAIN_WHEN_ERROR = ref(false);

// 定義菜單項目
const items = [
  {
    label: "購票網站",
    icon: "pi pi-server",
    items: [
      { label: "拓元", route: "/tixcraft" },
      { label: "遠大", disabled: true },
      { label: "KKTIX", disabled: true },
    ],
  },
];

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
  } finally {
    setting_visible.value = true; // 在請求後設置對話框顯示
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
</script>

<style scoped>
.title {
  font-family: "SuperCaramel"; /* 套用字體 */
  font-size: 1.5rem; /* 根據需要調整字體大小 */
  color: var(--p-text-color); /* 根據需要調整顏色 */
  margin-left: 0.5rem; /* 調整與圖片的間距 */
}

/* 調整右側設定按鈕的樣式 */
.p-menubar-end .p-button {
  margin-right: 0.5rem;
}
</style>

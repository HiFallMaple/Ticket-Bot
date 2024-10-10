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
        @click="visible=true"
      />
    </template>
  </Menubar>
  <SettingDialog v-model:visible="visible" />

</template>

<script setup>
import { ref } from "vue"; 
import Menubar from "primevue/menubar";
import Button from "primevue/button";
import SettingDialog from "./SettingDialog.vue";

const visible = ref(false);



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

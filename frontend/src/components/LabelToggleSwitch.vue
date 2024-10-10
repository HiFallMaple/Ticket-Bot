<template>
  <div class="flex flex-column">
    <h3>{{ label }}</h3>
    <small class="-mt-2 mb-2">{{ helpText }}</small>
    <ToggleSwitch v-model="modelValue" />
  </div>
</template>

<script setup>
import ToggleSwitch from "primevue/toggleswitch";

const modelValue = defineModel();
// 接收外部傳入的 props
const props = defineProps({
  label: String, // 標題文字
  helpText: String, // 小字說明文字
});
</script>

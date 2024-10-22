<template>
  <div class="flex flex-column">
    <h3>{{ label }}</h3>
    <small class="-mt-2 mb-2">{{ helpText }}</small>
    <TagInput v-model="modelValue" :placeholder="placeholder" />
  </div>
</template>

<script setup>
import TagInput from "@/components/TagInput.vue";

const modelValue = defineModel();
// 接收外部傳入的 props
const props = defineProps({
  label: String, // 標題文字
  helpText: String, // 小字說明文字
  placeholder: String,
});
</script>

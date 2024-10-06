<template>
  <div class="flex flex-column">
    <h3>{{ label }}</h3>
    <small class="-mt-2 mb-2" v-if="helpText" :id="inputId + '-help'">{{ helpText }}</small>
    <InputText
      :id="inputId"
      :value="modelValue"
      @input="updateValue"
      :placeholder="placeholder"
    />
  </div>
</template>

<script setup>
import InputText from "primevue/inputtext";

// 定義 props
const props = defineProps({
  modelValue: String,
  label: {
    type: String,
    required: true,
  },
  placeholder: {
    type: String,
    default: "請輸入...",
  },
  inputId: {
    type: String,
    default: "input-text",
  },
  helpText: {
    type: String,
    default: "",
  },
});

// 定義 emits
const emit = defineEmits(["update:modelValue"]);

// 更新輸入的值
const updateValue = (event) => {
  emit("update:modelValue", event.target.value);
};
</script>

<style scoped></style>

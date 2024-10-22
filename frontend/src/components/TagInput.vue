<template>
  <div>
    <div
      class="p-inputtext p-component flex flex-wrap py-0"
      style="min-height: 50px"
    >
      <div class="flex flex-wrap">
        <Chip
          v-for="(chip, index) in chips"
          :key="index"
          class="border-round-md"
          style="height: 38px; margin-top: 5px; margin-right: 5px"
        >
          <span class="">{{ chip }}</span>
          <button
            class="border-circle border-solid border-1 p-0"
            @click="removeChip(index)"
            style="height: 20px; width: 20px"
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 14 14"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              class="p-icon p-chip-remove-icon"
              aria-hidden="false"
              tabindex="0"
              data-pc-section="removeicon"
              style="margin-top: -1px; margin-left: -1px"
            >
              <path
                fill-rule="evenodd"
                clip-rule="evenodd"
                d="M4.66662 9.91668C4.58998 9.91704 4.51404 9.90209 4.44325 9.87271C4.37246 9.84333 4.30826 9.8001 4.2544 9.74557C4.14516 9.6362 4.0838 9.48793 4.0838 9.33335C4.0838 9.17876 4.14516 9.0305 4.2544 8.92113L6.17553 7L4.25443 5.07891C4.15139 4.96832 4.09529 4.82207 4.09796 4.67094C4.10063 4.51982 4.16185 4.37563 4.26872 4.26876C4.3756 4.16188 4.51979 4.10066 4.67091 4.09799C4.82204 4.09532 4.96829 4.15142 5.07887 4.25446L6.99997 6.17556L8.92106 4.25446C9.03164 4.15142 9.1779 4.09532 9.32903 4.09799C9.48015 4.10066 9.62434 4.16188 9.73121 4.26876C9.83809 4.37563 9.89931 4.51982 9.90198 4.67094C9.90464 4.82207 9.84855 4.96832 9.74551 5.07891L7.82441 7L9.74554 8.92113C9.85478 9.0305 9.91614 9.17876 9.91614 9.33335C9.91614 9.48793 9.85478 9.6362 9.74554 9.74557C9.69168 9.8001 9.62748 9.84333 9.55669 9.87271C9.4859 9.90209 9.40996 9.91704 9.33332 9.91668C9.25668 9.91704 9.18073 9.90209 9.10995 9.87271C9.03916 9.84333 8.97495 9.8001 8.9211 9.74557L6.99997 7.82444L5.07884 9.74557C5.02499 9.8001 4.96078 9.84333 4.88999 9.87271C4.81921 9.90209 4.74326 9.91704 4.66662 9.91668Z"
                fill="currentColor"
              ></path>
            </svg>
          </button>
        </Chip>
      </div>
      <input
        v-model="inputValue"
        @keydown.enter="addChip"
        @keydown.delete="handleDelete"
        @compositionend="handleCompositionEnd"
        :placeholder="actualPlaceholder"
        class="border-none p-0 m-0 bg-transparent appearance-none outline-none text-base"
        style="height: 48px"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from "vue";
import Chip from "primevue/chip";

const props = defineProps({
  placeholder: {
    type: String,
    required: true,
  },
  inputId: {
    type: String,
    default: "input-text",
  }
});

const inputValue = ref("");
const chips = defineModel();
const isComposing = ref(false);

const addChip = () => {
  if (!isComposing.value && inputValue.value.trim()) {
    chips.value.push(inputValue.value.trim());
    inputValue.value = "";
  }
};

// 處理刪除事件
const handleDelete = (event) => {
  if (inputValue.value.trim() === "" && chips.value.length > 0) {
    chips.value.pop(); // 刪除最後一個 Chip
  }
};

// 刪除指定索引的 Chip
const removeChip = (index) => {
  chips.value.splice(index, 1);
};

// 處理中文輸入法的組成事件
const handleCompositionEnd = () => {
  isComposing.value = false;
};

// 動態計算 placeholder
const actualPlaceholder = computed(() => {
  return chips.value.length > 0 ? "" : props.placeholder;
});

// watch(chips.value, (newValue) => {
//   console.log(newValue);
// });

</script>

<style scoped>
.p-inputtext-input {
  width: 100%;
  padding: 0.5rem;
}
</style>

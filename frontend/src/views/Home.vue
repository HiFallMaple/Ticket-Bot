<script setup>
import Button from "primevue/button";
import StatusDialog from "@/components/StatusDialog.vue";
</script>

<template>
  <StatusDialog />
  <div class="flex flex-column justify-content-center align-items-center m-0" style="height: calc(100vh - 100px)">
    <Button as="router-link" class="no-underline w-20rem h-7rem text-2xl mb-3" label="拓元" to="/tixcraft" />
    <Button class="no-underline w-20rem h-7rem text-2xl mb-3" label="遠大" disabled />
    <Button class="no-underline w-20rem h-7rem text-2xl mb-3" label="KKTIX" disabled />
  </div>
</template>

<style scoped>
</style>

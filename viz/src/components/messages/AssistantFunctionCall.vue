<script setup lang="ts">
import type { FunctionCall } from "@/kanpai/models";
import { ref } from "vue";

const props = defineProps<{
  functionCall: FunctionCall;
}>();

const isOpen = ref(true);
</script>

<template>
  <article class="message is-small">
    <div class="message-header">
      <p>Called {{ props.functionCall.name }}()...</p>
    </div>
    <div class="message-body" v-if="isOpen">
      <kbd>{{ functionCall.arguments }}</kbd>
    </div>
  </article>
</template>

<style scoped></style>
<script setup lang="ts">
import { FunctionCall } from "@/kanpai/models";
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
<!--      <button class="delete" aria-label="delete"></button>-->
    </div>
    <div class="message-body" v-if="isOpen">
      {{ functionCall.arguments }}
    </div>
  </article>
</template>

<style scoped></style>
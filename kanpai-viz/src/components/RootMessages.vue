<script setup lang="ts">
import type { ChatMessage } from "@/kanpai/models";

const props = defineProps<{
  messages: ChatMessage[];
}>();
</script>

<template>
  <p v-for="message in messages">
    {{ message.content}}
  </p>
  <p v-if="messages.length === 0">
    No messages yet!
  </p>
</template>

<style scoped></style>
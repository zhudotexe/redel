<script setup lang="ts">
import MessageContent from "@/components/messages/MessageContent.vue";
import type { ChatMessage } from "@/redel/models";

const props = defineProps<{
  message: ChatMessage;
}>();
</script>

<template>
  <div class="system-message">
    <div class="box has-text-centered mx-4 p-2">
      <MessageContent v-if="message.content" :content="props.message.content!" />
    </div>
  </div>
</template>

<style scoped lang="scss">
@import "./messages.scss";

.system-message {
  padding: 8px;
}
</style>

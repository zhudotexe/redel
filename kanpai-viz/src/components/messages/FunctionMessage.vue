<script setup lang="ts">
import type { ChatMessage } from "@/kanpai/models";

const props = defineProps<{
  message: ChatMessage;
}>();
</script>

<template>
  <div class="media">
    <figure class="media-left">
      <p class="image is-32x32"></p>
    </figure>
    <div class="media-content">
      <article class="message is-small">
        <div class="message-header">
          <p>Result</p>
        </div>
        <div class="message-body">
          {{ props.message.content }}
        </div>
      </article>
    </div>
  </div>
</template>

<style scoped>
.system-message {
  padding: 8px;
}
</style>
<script setup lang="ts">
import type { ChatMessage } from "@/kanpai/models";

const props = defineProps<{
  message: ChatMessage;
}>();
</script>

<template>
  <div class="media function-message">
    <figure class="media-left">
      <p class="image is-32x32"></p>
    </figure>
    <div class="media-content">
      <article class="message is-success is-small">
        <div class="message-body">
          {{ props.message.content }}
        </div>
      </article>
    </div>
  </div>
</template>

<style scoped>
.function-message {
  margin-top: -0.75em;
}
</style>
<script setup lang="ts">
import type { ChatMessage } from "@/redel/models";

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
          <p class="content allow-wrap-anywhere">
            {{ props.message.content }}
          </p>
        </div>
      </article>
    </div>
  </div>
</template>

<style scoped lang="scss">
@import "./messages.scss";

.function-message {
  margin-top: -0.75em;
}

/* https://stackoverflow.com/questions/36230944/prevent-flex-items-from-overflowing-a-container */
.media-content {
  min-width: 0;
}
</style>
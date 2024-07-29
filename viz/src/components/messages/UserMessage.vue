<script setup lang="ts">
import Markdown from "@/components/Markdown.vue";
import type { ChatMessage } from "@/redel/models";

const props = defineProps<{
  message: ChatMessage;
}>();
</script>

<template>
  <div class="media user-message">
    <figure class="media-left">
      <p class="image is-32x32">
        <img src="@/assets/twemoji/1f9d1-200d-1f4bb.svg" alt="User" />
      </p>
    </figure>
    <div class="media-content">
      <div class="content">
        <Markdown :content="props.message.content!" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.user-message {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 0.5em;
}
</style>

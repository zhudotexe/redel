<script setup lang="ts">
import Markdown from "@/components/Markdown.vue";
import type { ChatMessage } from "@/kanpai/models";

const props = defineProps<{
  message: ChatMessage;
}>();
</script>

<template>
  <div class="media">
    <figure class="media-left">
      <p class="image is-32x32">
        <img src="@/assets/twemoji/1f916.svg" alt="Assistant" />
      </p>
    </figure>
    <div class="media-content">
      <div class="content">
        <Markdown :content="props.message.content!" v-if="message.content" />
      </div>
    </div>
  </div>
</template>

<style scoped></style>
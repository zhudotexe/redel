<script setup lang="ts">
import Markdown from "@/components/Markdown.vue";
import AssistantFunctionCall from "@/components/messages/AssistantFunctionCall.vue";
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
      <div class="content" v-if="message.content">
        <Markdown :content="props.message.content!" />
      </div>
      <!-- function call -->
      <div v-if="message.tool_calls">
        <AssistantFunctionCall :function-call="tc.function" v-for="tc in message.tool_calls" />
      </div>
    </div>
  </div>
</template>

<style scoped></style>
<script setup lang="ts">
import AssistantFunctionCall from "@/components/messages/AssistantFunctionCall.vue";
import MessageContent from "@/components/messages/MessageContent.vue";
import type { ChatMessage } from "@/redel/models";

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
      <MessageContent v-if="message.content" :content="props.message.content!" />
      <!-- function call -->
      <div v-if="message.tool_calls">
        <AssistantFunctionCall :function-call="tc.function" v-for="tc in message.tool_calls" />
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
@import "./messages.scss";
</style>

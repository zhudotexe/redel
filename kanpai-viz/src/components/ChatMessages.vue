<script setup lang="ts">
import AssistantMessage from "@/components/messages/AssistantMessage.vue";
import AssistantStream from "@/components/messages/AssistantStream.vue";
import AssistantThinking from "@/components/messages/AssistantThinking.vue";
import FunctionMessage from "@/components/messages/FunctionMessage.vue";
import SystemMessage from "@/components/messages/SystemMessage.vue";
import UserMessage from "@/components/messages/UserMessage.vue";
import type { KanpaiClient } from "@/kanpai/client";
import { ChatRole, RunState } from "@/kanpai/models";
import type { KaniState } from "@/kanpai/state";
import { computed, inject, ref } from "vue";

const props = defineProps<{
  kani: KaniState;
}>();

const client = inject<KanpaiClient>("client")!;
const chatHistory = ref<HTMLElement | null>(null);

function scrollChatToBottom() {
  if (chatHistory.value === null) return;
  chatHistory.value.scrollTop = chatHistory.value.scrollHeight;
}

const streamBuffer = computed(() => {
  return client.streamMap.get(props.kani.id);
});

defineExpose({ scrollChatToBottom });
</script>

<template>
  <div class="messages" ref="chatHistory">
    <!-- complete messages -->
    <div v-for="message in kani.chat_history" class="chat-message">
      <UserMessage v-if="message.role === ChatRole.user" :message="message" class="user" />
      <AssistantMessage v-else-if="message.role === ChatRole.assistant" :message="message" />
      <FunctionMessage v-else-if="message.role === ChatRole.function" :message="message" />
      <SystemMessage v-else-if="message.role === ChatRole.system" :message="message" />
    </div>
    <!-- stream buffer -->
    <div class="chat-message" v-if="streamBuffer">
      <AssistantStream :content="streamBuffer" />
    </div>
    <!-- loading/nothing -->
    <p v-if="kani.chat_history.length === 0" class="chat-message">No messages yet!</p>
    <div class="chat-message" v-if="kani.state !== RunState.stopped && !streamBuffer">
      <AssistantThinking />
    </div>
    <div class="scroll-anchor"></div>
  </div>
</template>

<style scoped>
.messages {
  overflow: scroll;
}

.chat-message {
  overflow-anchor: none;
}

.chat-message > * {
  padding: 0.5em;
}

.scroll-anchor {
  height: 1px;
  overflow-anchor: auto;
}
</style>

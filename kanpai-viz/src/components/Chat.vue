<script setup lang="ts">
import AssistantMessage from "@/components/messages/AssistantMessage.vue";
import AssistantThinking from "@/components/messages/AssistantThinking.vue";
import FunctionMessage from "@/components/messages/FunctionMessage.vue";
import SystemMessage from "@/components/messages/SystemMessage.vue";
import UserMessage from "@/components/messages/UserMessage.vue";
import type { KanpaiClient } from "@/kanpai/client";
import { ChatRole, RunState } from "@/kanpai/models";
import autosize from "autosize";
import { onMounted, ref } from "vue";

const props = defineProps<{
  client: KanpaiClient;
}>();

const chatInput = ref<HTMLInputElement | null>(null);
const chatHistory = ref<HTMLElement | null>(null);
let chatMsg = ref("");

async function sendChatMsg() {
  const msg = chatMsg.value;
  if (msg.length === 0) return;
  chatMsg.value = "";
  props.client.sendMessage(msg);
  scrollChatToBottom();
  // wait for reply
  await props.client.waitForFullReply();
  setTimeout(() => {
    chatInput.value?.focus();
  }, 0);
}

function scrollChatToBottom() {
  if (chatHistory.value === null) return;
  chatHistory.value.scrollTop = chatHistory.value.scrollHeight;
}

onMounted(() => {
  autosize(chatInput.value!);
});
</script>

<template>
  <div class="messages" ref="chatHistory">
    <div v-for="message in client.rootMessages" class="chat-message">
      <UserMessage v-if="message.role === ChatRole.user" :message="message" class="user" />
      <AssistantMessage v-else-if="message.role === ChatRole.assistant" :message="message" />
      <FunctionMessage v-else-if="message.role === ChatRole.function" :message="message" />
      <SystemMessage v-else-if="message.role === ChatRole.system" :message="message" />
    </div>
    <p v-if="client.rootMessages.length === 0" class="chat-message">No messages yet!</p>
    <div class="chat-message" v-if="client.rootKani?.state !== RunState.stopped">
      <AssistantThinking />
    </div>
    <div class="scroll-anchor"></div>
  </div>
  <!-- msg bar -->
  <div class="chat-box">
    <textarea
      class="textarea has-fixed-size"
      :disabled="client.rootKani?.state !== RunState.stopped"
      autofocus
      rows="1"
      ref="chatInput"
      v-model.trim="chatMsg"
      @keydown.enter.exact.prevent="sendChatMsg"
    ></textarea>
  </div>
</template>

<style scoped>
.messages {
  overflow: scroll;
  max-height: 70vh;
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
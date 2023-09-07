<script setup lang="ts">
import AssistantMessage from "@/components/messages/AssistantMessage.vue";
import AssistantThinking from "@/components/messages/AssistantThinking.vue";
import SystemMessage from "@/components/messages/SystemMessage.vue";
import UserMessage from "@/components/messages/UserMessage.vue";
import type { KanpaiClient } from "@/kanpai/client";
import { ChatRole } from "@/kanpai/models";
import autosize from "autosize";
import { onMounted, ref } from "vue";

const props = defineProps<{
  client: KanpaiClient;
}>();

const chatInput = ref<HTMLInputElement | null>(null);
let chatMsg = ref("");
let aiThinking = ref(false);

async function sendChatMsg() {
  const msg = chatMsg.value;
  if (msg.length === 0) return;
  chatMsg.value = "";
  aiThinking.value = true;
  props.client.sendMessage(msg);
  await props.client.waitForFullReply();
  aiThinking.value = false;
  setTimeout(() => {
    chatInput.value?.focus();
  }, 0);
}

onMounted(() => {
  autosize(chatInput.value!);
});
</script>

<template>
  <div v-for="message in client.rootMessages" class="mb-2">
    <UserMessage v-if="message.role === ChatRole.user" :message="message" />
    <AssistantMessage v-else-if="message.role === ChatRole.assistant" :message="message" />
    <UserMessage v-else-if="message.role === ChatRole.function" :message="message" />
    <SystemMessage v-else-if="message.role === ChatRole.system" :message="message" />
  </div>
  <p v-if="client.rootMessages.length === 0" class="mb-2">No messages yet!</p>
  <div class="mb-2" v-if="aiThinking">
    <AssistantThinking />
  </div>
  <!-- msg bar -->
  <div>
    <textarea
      class="textarea has-fixed-size"
      :disabled="aiThinking"
      autofocus
      rows="1"
      ref="chatInput"
      v-model.trim="chatMsg"
      @keydown.enter.exact.prevent="sendChatMsg"
    ></textarea>
  </div>
</template>

<style scoped></style>

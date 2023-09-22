<script setup lang="ts">
import ChatMessages from "@/components/ChatMessages.vue";
import type { KanpaiClient } from "@/kanpai/client";
import { RunState } from "@/kanpai/models";
import autosize from "autosize";
import { inject, onMounted, ref } from "vue";

const client = inject<KanpaiClient>("client")!;
const chatInput = ref<HTMLInputElement | null>(null);
const chatMsg = ref("");
const chatMessages = ref<InstanceType<typeof ChatMessages> | null>(null);

async function sendChatMsg() {
  const msg = chatMsg.value;
  if (msg.length === 0) return;
  chatMsg.value = "";
  client.sendMessage(msg);
  chatMessages.value?.scrollChatToBottom();
  // wait for reply
  await client.waitForFullReply();
  setTimeout(() => {
    chatInput.value?.focus();
  }, 0);
}

onMounted(() => {
  autosize(chatInput.value!);
});
</script>

<template>
  <ChatMessages :kani="client.rootKani!" v-if="client.rootKani" ref="chatMessages" class="chat" />
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
.chat {
  max-height: 50vh;
}
</style>

<script setup lang="ts">
import ChatMessages from "@/components/ChatMessages.vue";
import type { KanpaiClient } from "@/kanpai/client";
import { RunState } from "@/kanpai/models";
import autosize from "autosize";
import { inject, nextTick, onMounted, ref } from "vue";

const client = inject<KanpaiClient>("client")!;
const chatInput = ref<HTMLInputElement | null>(null);
const chatMsg = ref("");
const chatMessages = ref<InstanceType<typeof ChatMessages> | null>(null);

async function sendChatMsg() {
  const msg = chatMsg.value.trim();
  if (msg.length === 0) return;
  chatMsg.value = "";
  nextTick(() => autosize.update(chatInput.value!));
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
  <div class="is-flex is-flex-direction-column mh-100">
    <!-- spacer -->
    <div class="spacer"></div>
    <!-- chat history -->
    <ChatMessages :kani="client.rootKani!" v-if="client.rootKani" ref="chatMessages" />
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
  </div>
</template>

<style scoped>
.spacer {
  flex: 1 0 auto;
}

.mh-100 {
  max-height: 100%;
}
</style>
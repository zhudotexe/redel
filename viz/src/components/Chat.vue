<script setup lang="ts">
import ChatMessages from "@/components/ChatMessages.vue";
import type { InteractiveClient } from "@/redel/interactive";
import { RunState } from "@/redel/models";
import type { ReDelState } from "@/redel/state";
import autosize from "autosize";
import { inject, nextTick, onMounted, ref } from "vue";

const client = inject<InteractiveClient>("client")!;
const state = inject<ReDelState>("state")!;

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
  <div class="is-flex is-flex-direction-column h-100">
    <div class="is-flex-grow-1"></div>
    <!-- chat history -->
    <ChatMessages :kani="state.rootKani!" v-if="state.rootKani" ref="chatMessages" />
    <!-- msg bar -->
    <div class="chat-box">
      <textarea
        class="textarea has-fixed-size"
        :disabled="state.rootKani?.state !== RunState.stopped"
        autofocus
        rows="1"
        ref="chatInput"
        v-model.trim="chatMsg"
        @keydown.enter.exact.prevent="sendChatMsg"
      ></textarea>
    </div>
  </div>
</template>

<style scoped></style>

<script setup lang="ts">
import Chat from "@/components/Chat.vue";
import Tree from "@/components/Tree.vue";
import { KanpaiClient } from "@/kanpai/client";
import { onMounted, onUnmounted, provide, reactive } from "vue";

const client = reactive(new KanpaiClient());

provide("client", client);

// hooks
onMounted(async () => {
  client.init();
  await client.getState();
});
onUnmounted(() => client.close());
</script>

<template>
  <div class="columns is-gapless main">
    <!-- root chat -->
    <div class="column">
      <div class="left-container">
        <h1 class="title">Kanpai!</h1>
        <div class="chat-container">
          <Chat />
        </div>
      </div>
    </div>
    <!-- viz -->
    <div class="column">
      <Tree />
    </div>
  </div>
</template>

<style scoped lang="scss">
@import "@/global.scss";

.main {
  height: 100vh;
}

.left-container {
  height: 100%;
  padding: 4rem 4rem 2rem 4rem;
  background: bulmaRgba($beige-light, 0.2);
}

.chat-container {
  height: calc(100% - 3.5rem);
}
</style>

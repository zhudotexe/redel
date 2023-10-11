<script setup lang="ts">
import Chat from "@/components/Chat.vue";
import ChatMessages from "@/components/ChatMessages.vue";
import Tree from "@/components/Tree.vue";
import { KanpaiClient } from "@/kanpai/client";
import type { KaniState } from "@/kanpai/state";
import { onMounted, onUnmounted, provide, reactive, ref } from "vue";

const client = reactive(new KanpaiClient());
const introspectedKani = ref<KaniState | null>(null);

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
      <div class="left-container is-flex is-flex-direction-column">
        <h1 class="title">Kanpai!</h1>
        <div class="chat-container">
          <Chat />
        </div>
      </div>
    </div>
    <!-- viz -->
    <div class="column">
      <div class="right-container is-flex is-flex-direction-column">
        <div class="is-flex-shrink-0">
          <Tree @node-clicked="(id) => (introspectedKani = client.kaniMap.get(id) ?? null)" />
        </div>
        <p v-if="introspectedKani" class="has-text-centered">
          Selected: {{ introspectedKani.name }}-{{ introspectedKani.depth }}
        </p>
        <div class="introspection-container">
          <ChatMessages :kani="introspectedKani" v-if="introspectedKani" />
          <p v-else>Click on a node on the tree above to view its state.</p>
        </div>
      </div>
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
  width: 50vw;
  padding: 4rem 4rem 2rem 4rem;
  background: bulmaRgba($beige-light, 0.2);
}

.chat-container {
  min-height: 0;
}

.right-container {
  max-height: 100%;
  width: 50vw;
}

.introspection-container {
  padding: 0 2rem;
  min-height: 0;
  overflow: scroll;
}
</style>

<script setup lang="ts">
import Chat from "@/components/Chat.vue";
import ChatMessages from "@/components/ChatMessages.vue";
import Tree from "@/components/Tree.vue";
import { InteractiveClient } from "@/kanpai/interactive";
import type { KaniState } from "@/kanpai/models";
import { onMounted, onUnmounted, provide, reactive, ref } from "vue";

const props = defineProps<{
  sessionId: string;
}>();

const client = reactive(new InteractiveClient(props.sessionId));
const introspectedKani = ref<KaniState | null>(null);
const tree = ref<InstanceType<typeof Tree> | null>(null);

provide("client", client);
provide("state", client.state);

// hooks
onMounted(async () => {
  // update tree on messages and state changes
  client.events.addEventListener("kani_message", () => tree.value?.update());
  client.events.addEventListener("kani_state_change", () => tree.value?.updateColors());

  // connect ws to backend, get state, update tree
  client.connect();
  await client.getState(); // todo what if this failed (e.g. user bookmarks a state) - probably redir to save?
  tree.value?.update();
});
onUnmounted(() => client.close());
</script>

<template>
  <div class="main">
    <div class="columns is-gapless h-100">
      <!-- root chat -->
      <div class="column">
        <div class="left-container chat-container">
          <Chat class="mt-auto" />
        </div>
      </div>
      <!-- viz -->
      <div class="column">
        <div class="right-container is-flex is-flex-direction-column">
          <div class="is-flex-shrink-0">
            <Tree
              @node-clicked="(id) => (introspectedKani = client.state.kaniMap.get(id) ?? null)"
              :selected-id="introspectedKani?.id"
              ref="tree"
            />
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
  background-color: rgba($beige-light, 0.2);
}

.chat-container {
  min-height: 0;
}

.right-container {
  max-height: 100%;
}

.introspection-container {
  padding: 0 2rem;
  min-height: 0;
  overflow: scroll;
}
</style>

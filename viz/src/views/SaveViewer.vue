<script setup lang="ts">
import ChatMessages from "@/components/ChatMessages.vue";
import Tree from "@/components/Tree.vue";
import { API } from "@/kanpai/api";
import { type BaseEvent, type KaniState } from "@/kanpai/models";
import { ReDelState } from "@/kanpai/state";
import { onMounted, provide, reactive, ref } from "vue";

const props = defineProps<{
  saveId: string;
}>();

const state = reactive<ReDelState>(new ReDelState());
const events = ref<BaseEvent[]>([]);
const introspectedKani = ref<KaniState | null>(null);
const tree = ref<InstanceType<typeof Tree> | null>(null);

provide("state", state);

// hooks
onMounted(async () => {
  // get state, update tree
  const sessionState = await API.getSaveState(props.saveId);
  state.loadSessionState(sessionState);
  tree.value?.update();
  // load events for replay
  events.value = await API.getSaveEvents(props.saveId);
});
</script>

<!-- similar to Interactive, but the Chat component is replaced with the replay controller -->
<template>
  <div class="main">
    <div class="columns is-gapless h-100" v-if="state">
      <!-- root chat -->
      <div class="column">
        <div class="left-container chat-container">
          <!-- Chat component, but messagebar replaced by replay controls -->
          <div class="is-flex is-flex-direction-column h-100">
            <div class="is-flex-grow-1"></div>
            <!-- chat history -->
            <ChatMessages :kani="state.rootKani!" v-if="state.rootKani" ref="chatMessages" />
            <!-- msg bar -->
            <div class="chat-box">TODO replay controls {{events.length}}</div>
          </div>
        </div>
      </div>
      <!-- viz -->
      <div class="column">
        <div class="right-container is-flex is-flex-direction-column">
          <div class="is-flex-shrink-0">
            <Tree
              @node-clicked="(id) => (introspectedKani = state!.kaniMap.get(id) ?? null)"
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
    <div v-else>Loading...</div>
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

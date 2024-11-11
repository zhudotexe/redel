<script setup lang="ts">
import ChatMessages from "@/components/ChatMessages.vue";
import Tree from "@/components/Tree.vue";
import { API } from "@/redel/api";
import { type BaseEvent, type KaniMessage, type KaniState } from "@/redel/models";
import { ReDelState } from "@/redel/state";
import { computed, nextTick, onMounted, provide, reactive, ref } from "vue";
import { useRouter } from "vue-router";

const props = defineProps<{
  saveId: string;
}>();

const router = useRouter();

const state = reactive<ReDelState>(new ReDelState());
const events = ref<BaseEvent[]>([]);
const replayIdx = ref<number>(0); // the index of the next event to play
const introspectedKaniId = ref<string | null>(null);
const tree = ref<InstanceType<typeof Tree> | null>(null);

provide("state", state);

const introspectedKani = computed<KaniState | undefined>(() => {
  if (!introspectedKaniId.value) return undefined;
  return state.kaniMap.get(introspectedKaniId.value);
});

// ===== replay utils =====
function setReplayTarget(idx: number) {
  if (idx < 0 || idx > events.value.length) return;
  const previousIdx = replayIdx.value;
  let needsTreeUpdate = false;
  // fwd
  if (previousIdx < idx) {
    const toReplay = events.value.slice(previousIdx, idx);
    for (const event of toReplay) {
      state.handleEvent(event);
    }
    needsTreeUpdate = toReplay.some((e) => e.type === "kani_message" || e.type === "kani_spawn");
  }
  // back
  else if (previousIdx > idx) {
    const toUndo = events.value.slice(idx, previousIdx).reverse();
    for (const event of toUndo) {
      state.undoEvent(event);
    }
    needsTreeUpdate = toUndo.some((e) => e.type === "kani_message" || e.type === "kani_spawn");
  }
  replayIdx.value = idx;
  if (needsTreeUpdate) tree.value?.update();
}

/**
 * Return the index immediately after the next kani_message event referencing this kani, or the current index if there
 * is none.
 */
function getNextMessageIdx(kani: KaniState): number {
  const idx = events.value
    .slice(replayIdx.value)
    .findIndex((e) => e.type === "kani_message" && (e as KaniMessage).id === kani.id);
  if (idx !== -1) return replayIdx.value + idx + 1;
  return replayIdx.value;
}

/**
 * Return the index of the previous kani_message or kani_spawn event referencing this kani, or the current index if
 * there is none.
 */
function getPreviousMessageIdx(kani: KaniState): number {
  if (!replayIdx.value) return replayIdx.value;
  const idx = events.value
    .slice(0, replayIdx.value)
    .reverse()
    .findIndex((e) => e.type === "kani_message" && (e as KaniMessage).id === kani.id);
  if (idx !== -1) return replayIdx.value - (idx + 1);
  return replayIdx.value;
}

// ===== save utils =====
async function loadSave(fork: boolean = false) {
  const newSessionState = await API.loadSaveToInteractive(props.saveId, fork);
  router.push({ name: "interactive", params: { sessionId: newSessionState.id } });
}

// hooks
onMounted(async () => {
  // get state, update tree
  const _sessionState = await API.getSaveState(props.saveId);
  events.value = await API.getSaveEvents(props.saveId);
  state.loadSessionState(_sessionState);
  // the slider doesn't like if the max and value are updated at the same time
  nextTick(() => {
    replayIdx.value = _sessionState.n_events;
  });
  tree.value?.update();
});
</script>

<!-- similar to Interactive, but the Chat component is replaced with the replay controller -->
<template>
  <div class="main">
    <div class="columns is-gapless h-100" v-if="state">
      <!-- root chat -->
      <div class="column is-flex is-flex-direction-column">
        <!-- toolbar -->
        <nav class="level is-mobile toolbar">
          <!-- Left side -->
          <div class="level-left">
            <div class="level-item">
              <p class="subtitle is-5">{{ state.meta?.title || "Untitled Session" }}</p>
            </div>
          </div>

          <!-- Right side -->
          <div class="level-right">
            <p class="level-item"><a class="button is-success" @click="loadSave(false)">Load</a></p>
            <p class="level-item"><a class="button is-success" @click="loadSave(true)">Fork</a></p>
          </div>
        </nav>

        <div class="left-container chat-container is-flex-grow-1">
          <!-- Chat component, but messagebar replaced by replay controls -->
          <div class="is-flex is-flex-direction-column h-100">
            <div class="is-flex-grow-1"></div>
            <!-- chat history -->
            <ChatMessages :kani="state.rootKani!" v-if="state.rootKani" ref="chatMessages" />
            <!-- replay controls -->
            <div class="box">
              <p class="is-size-7">You are viewing a saved session replay.</p>
              <div class="field is-grouped replay-controls">
                <!-- back 1 -->
                <p class="control" title="Go backward one event">
                  <button class="button is-info" @click="setReplayTarget(replayIdx - 1)">&lt;</button>
                </p>
                <!-- back selected -->
                <p class="control" title="Jump to previous message in selected node">
                  <button
                    class="button is-info"
                    @click="setReplayTarget(getPreviousMessageIdx(introspectedKani!))"
                    :disabled="introspectedKani === undefined"
                  >
                    &lt;&lt;
                  </button>
                </p>
                <!-- back root -->
                <p class="control" title="Jump to previous root message">
                  <button class="button is-info" @click="setReplayTarget(getPreviousMessageIdx(state.rootKani!))">
                    &lt;&lt;&lt;
                  </button>
                </p>
                <!-- slider -->
                <p class="control is-expanded">
                  <input
                    class="slider"
                    type="range"
                    :min="0"
                    :max="events.length"
                    :value="replayIdx"
                    @input="(e) => setReplayTarget(+(e.target as HTMLInputElement)?.value)"
                  />
                </p>
                <!-- fwd root -->
                <p class="control" title="Jump to next root message">
                  <button class="button is-info" @click="setReplayTarget(getNextMessageIdx(state.rootKani!))">
                    &gt;&gt;&gt;
                  </button>
                </p>
                <!-- fwd selected -->
                <p class="control" title="Jump to next message in selected node">
                  <button
                    class="button is-info"
                    :disabled="introspectedKani === undefined"
                    @click="setReplayTarget(getNextMessageIdx(introspectedKani!))"
                  >
                    &gt;&gt;
                  </button>
                </p>
                <!-- fwd 1 -->
                <p class="control" title="Go forward one event">
                  <button class="button is-info" @click="setReplayTarget(replayIdx + 1)">&gt;</button>
                </p>

                <p>{{ replayIdx }} / {{ events.length }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
      <!-- viz -->
      <div class="column">
        <div class="right-container is-flex is-flex-direction-column">
          <div class="is-flex-shrink-0">
            <Tree @node-clicked="(id) => (introspectedKaniId = id)" :selected-id="introspectedKaniId" ref="tree" />
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
  padding: 0 3rem 2rem 3rem;
  background-color: rgba($beige-light, 0.2);
}

.chat-container {
  min-height: 0;
}

.toolbar {
  margin: 0;
  padding: 0.5rem;
  border-bottom: 1px outset rgba($beige-light, 0.5);
}

.right-container {
  max-height: 100%;
}

.introspection-container {
  padding: 0 2rem;
  min-height: 0;
  overflow-y: auto;
}

///// replay controls /////
.replay-controls {
  align-items: center;
}

.slider {
  width: 100%;
  height: 100%;
}
</style>

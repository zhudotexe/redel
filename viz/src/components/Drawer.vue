<script setup lang="ts">
import LoadSaveModal from "@/components/LoadSaveModal.vue";
import SessionMetaRow from "@/components/SessionMetaRow.vue";
import { API } from "@/kanpai/api";
import type { SessionMeta } from "@/kanpai/models";
import { sorted } from "@/kanpai/utils";
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();

const isOpen = ref<boolean>(true);
const loadSaveModal = ref<InstanceType<typeof LoadSaveModal> | null>(null);
const interactiveSessions = ref<SessionMeta[]>([]);

async function startNewInteractive() {
  // request new interactive session, link to interactive
  const newState = await API.createStateInteractive();
  router.push({ name: "interactive", params: { sessionId: newState.id } });
}

async function updateInteractive() {
  interactiveSessions.value = await API.listStatesInteractive();
}

// hooks
onMounted(async () => {
  await updateInteractive();
});
router.afterEach(async () => {
  // update the session list on each navigation
  await updateInteractive();
});
</script>

<template>
  <aside class="menu drawer h-100" :class="{ closed: !isOpen, open: isOpen }">
    <div class="is-clipped">
      <div class="fixed-drawer-width">
        <RouterLink class="title" to="/">ReDel</RouterLink>
        <p class="menu-label">Controls</p>
        <ul class="menu-list">
          <li>
            <a @click="startNewInteractive">
              <span class="icon-text">
                <span class="icon is-small mt-1">
                  <font-awesome-icon :icon="['fas', 'circle-plus']" />
                </span>
                <span>Start a new session</span>
              </span>
            </a>
          </li>
          <li>
            <a @click="loadSaveModal!.open()">
              <span class="icon-text">
                <span class="icon is-small mt-1">
                  <font-awesome-icon :icon="['fas', 'folder-open']" />
                </span>
                <span>Load a saved session</span>
              </span>
            </a>
          </li>
        </ul>

        <p class="menu-label">Interactive Sessions</p>
        <ul class="menu-list">
          <li
            v-for="session in sorted(
              interactiveSessions,
              (a: SessionMeta, b: SessionMeta) => b.last_modified - a.last_modified,
            )"
          >
            <RouterLink :to="{ name: 'interactive', params: { sessionId: session.id } }" active-class="is-active">
              <SessionMetaRow :data="session" hide-icon-hints />
            </RouterLink>
          </li>
        </ul>
      </div>
    </div>

    <div class="drawer-handle has-text-weight-bold has-text-centered is-unselectable" @click="isOpen = !isOpen">
      {{ isOpen ? "&lt;" : "&gt;" }}
    </div>
  </aside>

  <LoadSaveModal ref="loadSaveModal" />
</template>

<style scoped lang="scss">
@import "@/global.scss";

$drawer-width: 16rem;
$drawer-padding: 1rem;
$handle-width: 0.75rem;
$handle-height: 3rem;

.drawer {
  position: relative;
  background-color: rgba($beige-light, 0.4);
  transition: width 300ms;
}

.open {
  width: $drawer-width;
}

.closed {
  width: 0;
}

.drawer-handle {
  position: absolute;
  right: -$handle-width;
  top: 50%;
  width: $handle-width;
  height: $handle-height;
  line-height: $handle-height;
  vertical-align: middle;
  border-radius: 0 4px 4px 0;
  background-color: rgba($beige-light, 0.5);
}

.drawer-handle:hover {
  background-color: rgba($beige-light, 1);
}

.fixed-drawer-width {
  width: $drawer-width - ($drawer-padding * 2);
  margin: $drawer-padding;
  overflow: hidden;
}
</style>

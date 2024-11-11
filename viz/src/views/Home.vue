<script setup lang="ts">
import LoadSaveModal from "@/components/LoadSaveModal.vue";
import { API } from "@/redel/api";
import autosize from "autosize";
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();

const chatInput = ref<HTMLInputElement | null>(null);
const chatMsg = ref("");
const loadSaveModal = ref<InstanceType<typeof LoadSaveModal> | null>(null);

async function sendChatMsg() {
  const msg = chatMsg.value.trim();
  if (msg.length === 0) return;
  chatMsg.value = "";
  chatInput.value!.disabled = true;
  // request new interactive session, link to interactive
  try {
    const newState = await API.createStateInteractive(msg);
    router.push({ name: "interactive", params: { sessionId: newState.id } });
  } catch (e) {
    chatInput.value!.disabled = false;
  }
}

onMounted(() => {
  autosize(chatInput.value!);
});
</script>

<template>
  <div class="main is-flex is-flex-direction-column has-text-centered">
    <div class="is-flex-grow-2"></div>

    <div class="columns is-mobile is-multiline is-centered">
      <div class="column is-narrow">
        <div class="box">
          <h1 class="title">Welcome to ReDel's web interface!</h1>
          <h2 class="subtitle">
            Here, you can interact with the configured ReDel system, view previous logs, and resume from old saves.
          </h2>
        </div>
      </div>
    </div>

    <!-- action boxes -->
    <div class="columns is-mobile is-multiline is-centered">
      <div class="column is-narrow">
        <div class="box hover-darken is-clickable" @click="loadSaveModal!.open()">
          <div class="has-text-primary">
            <span class="icon">
              <font-awesome-icon :icon="['fas', 'folder-open']" />
            </span>
          </div>
          <p>Load a saved session</p>
        </div>
      </div>
      <div class="column is-narrow">
        <a href="https://aclanthology.org/2024.emnlp-demo.17/" target="_blank">
          <div class="box hover-darken">
            <div class="has-text-success">
              <span class="icon">
                <font-awesome-icon :icon="['fas', 'book-open']" />
              </span>
            </div>
            <p class="icon-text">
              <span>Read the paper</span>
              <span class="icon">
                <font-awesome-icon :icon="['fas', 'arrow-up-right-from-square']" />
              </span>
            </p>
          </div>
        </a>
      </div>
      <div class="column is-narrow">
        <a href="https://github.com/zhudotexe/redel" target="_blank">
          <div class="box hover-darken">
            <div>
              <span class="icon">
                <font-awesome-icon :icon="['fab', 'github']" />
              </span>
            </div>
            <p class="icon-text">
              <span>View the code on GitHub</span>
              <span class="icon">
                <font-awesome-icon :icon="['fas', 'arrow-up-right-from-square']" />
              </span>
            </p>
          </div>
        </a>
      </div>
    </div>

    <div class="is-flex-grow-1"></div>

    <!-- chatbox -->
    <div class="columns is-mobile is-multiline is-centered">
      <div class="column is-10-tablet is-6-desktop">
        <div class="chat-box">
          <textarea
            class="textarea has-fixed-size"
            autofocus
            rows="1"
            placeholder="Or type here to start a new session..."
            ref="chatInput"
            v-model.trim="chatMsg"
            @keydown.enter.exact.prevent="sendChatMsg"
          ></textarea>
        </div>
      </div>
    </div>

    <div class="is-flex-grow-2"></div>
  </div>

  <LoadSaveModal ref="loadSaveModal" />
</template>

<style scoped>
.main {
  height: 100vh;
}

.hover-darken:hover {
  background-color: rgba(255, 255, 255, 0.7);
}
</style>

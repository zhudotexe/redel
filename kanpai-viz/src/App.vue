<script setup lang="ts">
import RootMessages from "@/components/RootMessages.vue";
import { KanpaiClient } from "@/kanpai/client";
import { onMounted, onUnmounted, reactive } from "vue";

const client = reactive(new KanpaiClient());

// hooks
onMounted(async () => {
  client.init();
  await client.getState();
});
onUnmounted(() => client.close());
</script>

<template>
  <!-- root chat -->
  <section class="hero is-primary root-chat">
    <div class="hero-body">
      <div class="container">
        <h1 class="title">Kanpai!</h1>
        <RootMessages :messages="client.rootMessages" />
      </div>
    </div>
  </section>

  <!-- viz -->
  <section class="section">
    <div class="container"></div>
  </section>
</template>

<style scoped>
.root-chat {
  max-height: 75vh;
}
</style>
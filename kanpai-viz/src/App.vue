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
  <!-- root chat -->
  <section class="hero is-primary">
    <div class="hero-body">
      <div class="container">
        <h1 class="title">Kanpai!</h1>
        <Chat />
      </div>
    </div>
  </section>

  <!-- viz -->
  <section class="section">
    <div class="container">
      <Tree />
    </div>
  </section>
</template>

<style scoped></style>
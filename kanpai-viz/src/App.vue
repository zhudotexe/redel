<script setup lang="ts">
import Chat from "@/components/Chat.vue";
import Tree from "@/components/Tree.vue";
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
  <section class="hero is-primary">
    <div class="hero-body">
      <div class="container">
        <h1 class="title">Kanpai!</h1>
        <Chat :client="client" />
      </div>
    </div>
  </section>

  <!-- viz -->
  <section class="section">
    <div class="container">
      <Tree :client="client" />
    </div>
  </section>
</template>

<style scoped></style>
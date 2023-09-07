<script setup lang="ts">
import Markdown from "@/components/Markdown.vue";
import type { ChatMessage } from "@/kanpai/models";

const props = defineProps<{
  message: ChatMessage;
}>();
</script>

<template>
  <div class="box has-text-centered mx-4">
    <div class="content">
      <Markdown :content="props.message.content!" />
    </div>
  </div>
</template>

<style scoped></style>

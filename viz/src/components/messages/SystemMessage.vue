<script setup lang="ts">
import Markdown from "@/components/Markdown.vue";
import type { ChatMessage } from "@/redel/models";

const props = defineProps<{
  message: ChatMessage;
}>();
</script>

<template>
  <div class="system-message">
    <div class="box has-text-centered mx-4 p-2">
      <div class="content allow-wrap-anywhere">
        <Markdown :content="props.message.content!" />
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
@import "./messages.scss";

.system-message {
  padding: 8px;
}
</style>

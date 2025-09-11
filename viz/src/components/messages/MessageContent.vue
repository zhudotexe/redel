<script setup lang="ts">
import Markdown from "@/components/Markdown.vue";
import { computed } from "vue";

const props = defineProps<{
  content: string | any[] | null;
}>();

const contentParts = computed(() => {
  if (typeof props.content === "string") {
    return [props.content];
  } else if (!props.content) {
    return [];
  }

  let parts: any[] = [];
  let lastStringContent = "";
  for (const part of props.content) {
    if (typeof part === "string") {
      lastStringContent += part;
    } else {
      if (lastStringContent) {
        parts.push(lastStringContent);
        lastStringContent = "";
      }
      parts.push(part);
    }
  }
  if (lastStringContent) {
    parts.push(lastStringContent);
  }

  return parts;
});
</script>

<template>
  <div class="content allow-wrap-anywhere">
    <template v-for="part in contentParts">
      <Markdown v-if="typeof part === 'string'" :content="part" />
      <details v-else>
        <summary>Unrendered data</summary>
        <pre>{{ part }}</pre>
      </details>
    </template>
  </div>
</template>

<style scoped lang="scss"></style>

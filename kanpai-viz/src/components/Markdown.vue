<script setup lang="ts">
import MarkdownIt from "markdown-it";
import MarkdownItHighlightjs from "markdown-it-highlightjs";

const props = defineProps<{
  content: string;
}>();

const markdown = new MarkdownIt().use(MarkdownItHighlightjs);
</script>

<template>
  <p v-html="markdown.render(props.content)"></p>
</template>

<style scoped></style>
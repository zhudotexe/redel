<script setup lang="ts">
import MarkdownIt from "markdown-it";
import MarkdownItHighlightjs from "markdown-it-highlightjs";

const props = defineProps<{
  content: string;
}>();

const markdown = new MarkdownIt({ breaks: true, linkify: true }).use(MarkdownItHighlightjs);
</script>

<template>
  <p class="markdown" v-html="markdown.render(props.content)"></p>
</template>

<style scoped lang="scss">
.markdown:deep(pre) {
  white-space: pre-wrap !important;
}
</style>

<script setup lang="ts">
import NotificationsOverlay from "@/components/NotificationsOverlay.vue";
</script>

<template>
  <router-view />
  <NotificationsOverlay />
</template>

<style lang="scss">
@import "@/global.scss";
</style>

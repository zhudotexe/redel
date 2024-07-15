<script setup lang="ts">
import Drawer from "@/components/Drawer.vue";
import NotificationsOverlay from "@/components/NotificationsOverlay.vue";
</script>

<template>
  <div class="main-container">
    <div>
      <Drawer />
    </div>
    <div class="is-flex-grow-1">
      <router-view :key="$route.fullPath" />
    </div>
  </div>
  <NotificationsOverlay />
</template>

<style lang="scss">
@import "@/global.scss";

.main-container {
  display: flex;
}
</style>

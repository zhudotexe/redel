<script setup lang="ts">
import { NotificationLevel, Notifications } from "@/redel/notifications";
</script>

<template>
  <Teleport to="body">
    <div class="notifications">
      <div
        v-for="notification in Notifications.notifs"
        class="notification"
        :class="{
          'is-info': notification.level === NotificationLevel.info,
          'is-success': notification.level === NotificationLevel.success,
          'is-warning': notification.level === NotificationLevel.warning,
          'is-danger': notification.level === NotificationLevel.danger,
        }"
      >
        <button class="delete" @click="Notifications.dismiss(notification)"></button>
        {{ notification.message }}
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.notifications {
  position: fixed;
  top: 1em;
  right: 1em;
}
</style>

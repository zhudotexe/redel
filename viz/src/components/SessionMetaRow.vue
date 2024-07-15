<script setup lang="ts">
import type { SessionMeta } from "@/kanpai/models";

interface Props {
  data: SessionMeta;
  showPath?: string[];
  hideIconHints?: boolean;
}

defineProps<Props>();
</script>

<template>
  <div>
    <!-- break out of the flex ctx with div -->
    <p>{{ data.title ?? `&lt;No title - ID ${data.id}&gt;` }}</p>
    <p class="is-size-7">
      <span class="icon-text icon-text-fix">
        <template v-if="showPath">
          <span class="icon small-icon-fix">
            <font-awesome-icon :icon="['fas', 'file']" />
          </span>
          <span> {{ hideIconHints ? "" : "Found in " }}{{ showPath.join("/") }} </span>
        </template>

        <span class="icon small-icon-fix">
          <font-awesome-icon :icon="['fas', 'calendar-day']" />
        </span>
        <span>
          {{ hideIconHints ? "" : "Last modified " }}{{ new Date(data.last_modified * 1000).toLocaleString() }}
        </span>

        <span class="icon small-icon-fix">
          <font-awesome-icon :icon="['fas', 'hashtag']" />
        </span>
        <span>{{ data.n_events }} events</span>
      </span>
    </p>
  </div>
</template>

<style scoped>
.small-icon-fix {
  margin-right: -0.5em;
}

.icon-text-fix {
  margin-left: -0.5em;
}
</style>

<script setup lang="ts">
import SessionMetaRow from "@/components/SessionMetaRow.vue";
import { API } from "@/kanpai/api";
import type { SaveMeta } from "@/kanpai/models";
import { sorted } from "@/kanpai/utils";
import { computed, ref } from "vue";

/**
 * Helper class to organize the saves from a flat list to a traditional filetree
 */
class Directory {
  name: string;
  subdirs: Map<string, Directory>;
  saves: SaveMeta[]; // all saves that are immediate children of this dir
  allChildSaves: SaveMeta[]; // all saves that are eventual children of this dir

  constructor(name: string) {
    this.name = name;
    this.subdirs = new Map<string, Directory>();
    this.saves = [];
    this.allChildSaves = [];
  }

  // thin: this directory contains only one child directory
  get isThin(): boolean {
    return this.subdirs.size === 1 && this.saves.length === 0;
  }

  get thinParts(): string[] {
    if (!this.isThin) return [this.name];
    const child = this.subdirs.values().next().value;
    return [this.name, ...child.thinParts];
  }

  get thinName(): string {
    return this.thinParts.join("/");
  }

  public clear() {
    this.subdirs.clear();
    this.saves = [];
    this.allChildSaves = [];
  }
}

////////// vue //////////
const isOpen = ref(false);
const searchQuery = ref<string>("");
const dirPrefix = ref<string[]>([]); // prefix relative to root
const sortCompareFn = ref<(a: SaveMeta, b: SaveMeta) => number>((a, b) => b.id.localeCompare(a.id));

// computed props
const saves = ref<SaveMeta[]>([]);
const tree = ref<Directory>(new Directory("root"));

// on open, reset state
async function open() {
  isOpen.value = true;
  searchQuery.value = "";
  // dirPrefix.value = [];
  saves.value = await API.listSaves();
  // compute the full filetree now
  computeFileTree();
}

// expose attrs for controller
defineExpose({ open });

const currentDir = computed<Directory>(() => {
  let current = tree.value;
  for (const part of dirPrefix.value) {
    current = current.subdirs.get(part)!;
  }
  return current;
});

const searchMatchSaves = computed<SaveMeta[]>(() => {
  const tokens = searchQuery.value.toLocaleLowerCase().split(/\s+/);
  return saves.value.filter((save) => tokens.every((token) => save.title?.toLocaleLowerCase().includes(token)));
});

////////// internal logic //////////
function computeFileTree() {
  tree.value.clear();
  // build up the tree
  for (const save of saves.value) {
    let currentDir = tree.value;
    for (const part of save.grouping_prefix) {
      // add the save as an eventual child of the dir
      currentDir.allChildSaves.push(save);
      // and walk the subdirs
      if (!currentDir.subdirs.has(part)) {
        currentDir.subdirs.set(part, new Directory(part));
      }
      currentDir = currentDir.subdirs.get(part)!;
    }
    currentDir.saves.push(save);
  }
  // while our root only has a single subdir, enter it
  while (tree.value.isThin) {
    tree.value = tree.value.subdirs.values().next().value;
  }
}
</script>

<template>
  <Teleport to="body">
    <div class="modal is-active" v-if="isOpen">
      <div class="modal-background"></div>
      <div class="modal-content wider-modal">
        <!-- Save navigation tree -->
        <nav class="panel">
          <p class="panel-heading">Load saved session</p>
          <!-- search, sort -->
          <div class="panel-block">
            <div class="field is-grouped is-flex-grow-1">
              <div class="control has-icons-left is-expanded">
                <input class="input" type="text" placeholder="Search" v-model="searchQuery" />
                <span class="icon is-left">
                  <font-awesome-icon :icon="['fas', 'search']" />
                </span>
              </div>

              <div class="control">
                <div class="select">
                  <select v-model="sortCompareFn">
                    <option :value="(a: SaveMeta, b: SaveMeta) => b.id.localeCompare(a.id)">Sort by ID</option>
                    <option
                      :value="
                        (a: SaveMeta, b: SaveMeta) => {
                          if (a.title && b.title) {
                            return a.title.localeCompare(b.title);
                          } else if (a.title) {
                            return -9999;
                          } else if (b.title) {
                            return 9999;
                          } else {
                            return b.id.localeCompare(a.id);
                          }
                        }
                      "
                    >
                      Sort by name
                    </option>
                    <option :value="(a: SaveMeta, b: SaveMeta) => b.last_modified - a.last_modified">
                      Sort by last edited
                    </option>
                    <option :value="(a: SaveMeta, b: SaveMeta) => b.n_events - a.n_events">Sort by event count</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
          <!-- no search -->
          <template v-if="!searchQuery">
            <!-- breadcrumbs -->
            <div class="panel-block">
              <nav class="breadcrumb" aria-label="breadcrumbs">
                <ul>
                  <li>
                    <a @click="dirPrefix = []">{{ tree.name }}</a>
                  </li>
                  <li v-for="(part, idx) in dirPrefix">
                    <a @click="dirPrefix = dirPrefix.slice(0, idx + 1)">{{ part }}</a>
                  </li>
                  <li></li>
                </ul>
              </nav>
            </div>

            <!-- tree - dirs -->
            <a
              class="panel-block"
              v-for="dir in sorted(currentDir.subdirs.values(), (a, b) => a.name.localeCompare(b.name))"
              @click="dirPrefix.push(...dir.thinParts)"
            >
              <span class="panel-icon">
                <font-awesome-icon :icon="['fas', 'folder-open']" />
              </span>
              {{ dir.thinName }}
            </a>

            <!-- tree - saves -->
            <RouterLink
              v-for="save in sorted(currentDir.saves, sortCompareFn)"
              class="panel-block"
              active-class="is-active"
              :to="{ name: 'save', params: { saveId: save.id } }"
              @click="isOpen = false"
            >
              <span class="panel-icon">
                <font-awesome-icon :icon="['fas', 'diagram-project']" />
              </span>
              <SessionMetaRow :data="save" />
            </RouterLink>
          </template>

          <!-- search -->
          <template v-else>
            <!-- matching saves -->
            <RouterLink
              v-for="save in sorted(searchMatchSaves, sortCompareFn)"
              class="panel-block"
              active-class="is-active"
              :to="{ name: 'save', params: { saveId: save.id } }"
              @click="isOpen = false"
            >
              <span class="panel-icon">
                <font-awesome-icon :icon="['fas', 'diagram-project']" />
              </span>
              <SessionMetaRow :data="save" :show-path="save.grouping_prefix" />
            </RouterLink>
          </template>
        </nav>
      </div>
      <button class="modal-close is-large" aria-label="close" @click="isOpen = false"></button>
    </div>
  </Teleport>
</template>

<style scoped>
.wider-modal {
  width: max(66%, var(--bulma-modal-content-width));
}

.panel {
  background-color: white;
}
</style>

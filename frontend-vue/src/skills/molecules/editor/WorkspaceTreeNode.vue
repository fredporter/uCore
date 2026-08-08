<template>
  <!-- File node -->
  <div
    v-if="node.type === 'file'"
    class="tree-node tree-node--file"
    :class="{ 'tree-node--selected': selectedId === node.id }"
    :style="{ paddingLeft: `${8 + depth * 16}px` }"
    role="treeitem"
    :aria-selected="selectedId === node.id"
    @click="emit('select', node)"
    @contextmenu.prevent="showMenu($event)"
  >
    <UIcon :name="fileIcon" class="tree-node__icon" />
    <span class="tree-node__name">{{ node.name }}</span>
  </div>

  <!-- Folder node -->
  <div v-else class="tree-node-folder">
    <div
      class="tree-node tree-node--folder"
      :style="{ paddingLeft: `${8 + depth * 16}px` }"
      role="treeitem"
      :aria-expanded="isExpanded"
      @click="emit('toggle', node.id)"
      @contextmenu.prevent="showMenu($event)"
    >
      <UIcon
        :name="isExpanded ? 'expand_more' : 'chevron_right'"
        class="tree-node__chevron"
      />
      <UIcon name="folder" class="tree-node__icon tree-node__icon--folder" />
      <span class="tree-node__name">{{ node.name }}</span>
    </div>

    <!-- Children (when expanded) -->
    <div v-if="isExpanded && node.children?.length" class="tree-node-children">
      <WorkspaceTreeNode
        v-for="child in node.children"
        :key="child.id"
        :node="child"
        :depth="depth + 1"
        :selected-id="selectedId"
        :expanded-ids="expandedIds"
        @select="emit('select', $event)"
        @toggle="emit('toggle', $event)"
        @delete="emit('delete', $event)"
        @rename="emit('rename', $event)"
        @create="emit('create', $event)"
      />
    </div>

    <!-- Empty folder hint -->
    <div
      v-if="isExpanded && !node.children?.length"
      class="tree-node-empty"
      :style="{ paddingLeft: `${24 + depth * 16}px` }"
    >
      empty
    </div>
  </div>

  <!-- Context menu -->
  <Teleport to="body">
    <div
      v-if="menuVisible"
      class="tree-context-menu"
      :style="{ top: `${menuY}px`, left: `${menuX}px` }"
      @mouseleave="closeMenu"
    >
      <button
        v-if="node.type === 'folder'"
        class="tree-context-menu__item"
        @click="onCreateFile"
      >
        <UIcon name="note_add" /> New file
      </button>
      <button
        v-if="node.type === 'folder'"
        class="tree-context-menu__item"
        @click="onCreateFolder"
      >
        <UIcon name="create_new_folder" /> New folder
      </button>
      <div v-if="node.type === 'folder'" class="tree-context-menu__divider" />
      <button class="tree-context-menu__item" @click="onRename">
        <UIcon name="edit" /> Rename
      </button>
      <button
        class="tree-context-menu__item tree-context-menu__item--danger"
        @click="onDelete"
      >
        <UIcon name="delete" /> Delete
      </button>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onBeforeUnmount } from "vue";
import type { FileNode } from "../../../stores/workspace";
import UIcon from "../../atoms/UIcon.vue";

interface Props {
  node: FileNode;
  depth: number;
  selectedId: string | null;
  expandedIds: Set<string>;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  select: [node: FileNode];
  toggle: [id: string];
  delete: [id: string];
  rename: [node: FileNode];
  create: [payload: { type: "file" | "folder"; parentPath: string }];
}>();

const isExpanded = computed(() => props.expandedIds.has(props.node.id));

const FILE_ICONS: Record<string, string> = {
  md: "description",
  txt: "text_snippet",
  ts: "code",
  js: "code",
  json: "data_object",
  yaml: "settings",
  yml: "settings",
  css: "css",
  html: "html",
};

const fileIcon = computed(
  () => FILE_ICONS[props.node.extension ?? ""] ?? "draft",
);

// ─── Context menu ─────────────────────────────────────────────
const menuVisible = ref(false);
const menuX = ref(0);
const menuY = ref(0);

function showMenu(event: MouseEvent) {
  menuX.value = event.clientX;
  menuY.value = event.clientY;
  menuVisible.value = true;
}

function closeMenu() {
  menuVisible.value = false;
}

function onCreateFile() {
  closeMenu();
  emit("create", { type: "file", parentPath: props.node.path });
}

function onCreateFolder() {
  closeMenu();
  emit("create", { type: "folder", parentPath: props.node.path });
}

function onRename() {
  closeMenu();
  emit("rename", props.node);
}

function onDelete() {
  closeMenu();
  if (window.confirm(`Delete "${props.node.name}"?`)) {
    emit("delete", props.node.id);
  }
}

function handleGlobalClick() {
  if (menuVisible.value) closeMenu();
}

onMounted(() => document.addEventListener("click", handleGlobalClick));
onBeforeUnmount(() => document.removeEventListener("click", handleGlobalClick));
</script>

<style scoped>
.tree-node {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding-top: 3px;
  padding-bottom: 3px;
  padding-right: var(--usx-spacing-sm);
  cursor: pointer;
  border-radius: 0;
  transition: background-color 100ms ease;
  user-select: none;
}

.tree-node:hover {
  background-color: color-mix(
    in srgb,
    var(--usx-color-primary) 8%,
    transparent
  );
}

.tree-node--selected {
  background-color: color-mix(
    in srgb,
    var(--usx-color-primary) 16%,
    transparent
  );
}

.tree-node--selected .tree-node__name {
  color: var(--usx-color-primary);
  font-weight: var(--usx-font-weight-medium);
}

.tree-node__chevron {
  font-size: 16px;
  color: var(--usx-color-on-surface-muted);
  flex-shrink: 0;
  width: 16px;
}

.tree-node__icon {
  font-size: 14px;
  color: var(--usx-color-on-surface-muted);
  flex-shrink: 0;
}

.tree-node__icon--folder {
  color: var(--usx-color-warning);
}

.tree-node--selected .tree-node__icon {
  color: var(--usx-color-primary);
}

.tree-node__name {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface);
  truncate: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tree-node-empty {
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
  padding-top: 2px;
  padding-bottom: 2px;
  opacity: 0.6;
  font-style: italic;
}

/* ─── Context menu ────────────────────────────────────────────── */

.tree-context-menu {
  position: fixed;
  z-index: 9000;
  background-color: var(--usx-color-surface);
  border: 1px solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  padding: var(--usx-spacing-xs);
  min-width: 160px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.tree-context-menu__item {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: var(--usx-radius-sm);
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-sm);
  font-family: var(--usx-font-family-sans);
  text-align: left;
  transition: background-color 100ms ease;
}

.tree-context-menu__item:hover {
  background-color: var(--usx-color-background);
}

.tree-context-menu__item--danger {
  color: var(--usx-color-danger);
}

.tree-context-menu__divider {
  height: 1px;
  background-color: var(--usx-color-border);
  margin: 2px 0;
}
</style>

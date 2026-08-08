<template>
  <div class="workspace-tree">
    <!-- Header with new-file / new-folder buttons -->
    <div class="workspace-tree__header">
      <span class="workspace-tree__heading">Files</span>
      <div class="workspace-tree__actions">
        <button
          class="workspace-tree__action-btn"
          title="New file"
          @click="promptCreate('file')"
        >
          <UIcon name="note_add" />
        </button>
        <button
          class="workspace-tree__action-btn"
          title="New folder"
          @click="promptCreate('folder')"
        >
          <UIcon name="create_new_folder" />
        </button>
      </div>
    </div>

    <!-- Breadcrumb when file is selected -->
    <div v-if="ws.breadcrumb.length > 0" class="workspace-tree__breadcrumb">
      <span
        v-for="(crumb, i) in ws.breadcrumb"
        :key="i"
        class="workspace-tree__crumb"
      >
        <span v-if="i > 0" class="workspace-tree__crumb-sep">/</span>
        {{ crumb }}
      </span>
    </div>

    <!-- Tree -->
    <div class="workspace-tree__list" role="tree">
      <WorkspaceTreeNode
        v-for="node in ws.tree"
        :key="node.id"
        :node="node"
        :depth="0"
        :selected-id="ws.selectedId"
        :expanded-ids="ws.expandedIds"
        @select="ws.selectFile"
        @toggle="ws.toggleFolder"
        @delete="ws.deleteNode"
        @rename="handleRename"
        @create="handleCreate"
      />
    </div>

    <!-- Inline create dialog -->
    <div v-if="createDialog.visible" class="workspace-tree__create-dialog">
      <UIcon :name="createDialog.type === 'file' ? 'note_add' : 'folder'" />
      <input
        ref="createInputEl"
        v-model="createDialog.name"
        class="workspace-tree__create-input"
        :placeholder="
          createDialog.type === 'file' ? 'filename.md' : 'Folder name'
        "
        @keydown.enter="confirmCreate"
        @keydown.escape="cancelCreate"
        @blur="cancelCreate"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from "vue";
import { useWorkspaceStore, type FileNode } from "../../../stores/workspace";
import WorkspaceTreeNode from "./WorkspaceTreeNode.vue";
import UIcon from "../../atoms/UIcon.vue";

const ws = useWorkspaceStore();
const createInputEl = ref<HTMLInputElement | null>(null);

const createDialog = ref<{
  visible: boolean;
  type: "file" | "folder";
  parentPath: string;
  name: string;
}>({ visible: false, type: "file", parentPath: "/", name: "" });

async function promptCreate(type: "file" | "folder", parentPath = "/") {
  createDialog.value = { visible: true, type, parentPath, name: "" };
  await nextTick();
  createInputEl.value?.focus();
}

function confirmCreate() {
  const { type, parentPath, name } = createDialog.value;
  if (!name.trim()) return cancelCreate();

  const safeName = type === "file" && !name.includes(".") ? `${name}.md` : name;
  if (type === "file") {
    ws.createFile(parentPath, safeName);
  } else {
    ws.createFolder(parentPath, safeName);
  }
  cancelCreate();
}

function cancelCreate() {
  createDialog.value.visible = false;
}

function handleRename(node: FileNode) {
  const newName = window.prompt("Rename:", node.name);
  if (newName && newName.trim() && newName !== node.name) {
    ws.renameNode(node.id, newName.trim());
  }
}

function handleCreate(payload: {
  type: "file" | "folder";
  parentPath: string;
}) {
  promptCreate(payload.type, payload.parentPath);
}
</script>

<style scoped>
.workspace-tree {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: var(--usx-color-surface-variant);
  border-right: 1px solid var(--usx-color-border);
  overflow: hidden;
}

/* ─── Header ──────────────────────────────────────────────────── */

.workspace-tree__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border-bottom: 1px solid var(--usx-color-border);
  flex-shrink: 0;
}

.workspace-tree__heading {
  font-size: var(--usx-font-size-xs);
  font-weight: var(--usx-font-weight-semibold);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--usx-color-on-surface-muted);
}

.workspace-tree__actions {
  display: flex;
  gap: var(--usx-spacing-xs);
}

.workspace-tree__action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: var(--usx-radius-sm);
  color: var(--usx-color-on-surface-muted);
  transition: all 120ms ease;
}

.workspace-tree__action-btn:hover {
  background-color: var(--usx-color-border);
  color: var(--usx-color-on-surface);
}

/* ─── Breadcrumb ──────────────────────────────────────────────── */

.workspace-tree__breadcrumb {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 2px;
  padding: var(--usx-spacing-xs) var(--usx-spacing-md);
  border-bottom: 1px solid var(--usx-color-border);
  background-color: var(--usx-color-background);
  flex-shrink: 0;
}

.workspace-tree__crumb {
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
}

.workspace-tree__crumb:last-child {
  color: var(--usx-color-primary);
  font-weight: var(--usx-font-weight-medium);
}

.workspace-tree__crumb-sep {
  margin-right: 2px;
  opacity: 0.5;
}

/* ─── List ────────────────────────────────────────────────────── */

.workspace-tree__list {
  flex: 1;
  overflow-y: auto;
  padding: var(--usx-spacing-xs) 0;
}

.workspace-tree__list::-webkit-scrollbar {
  width: 4px;
}

.workspace-tree__list::-webkit-scrollbar-thumb {
  background-color: var(--usx-color-border);
  border-radius: 2px;
}

/* ─── Create dialog ───────────────────────────────────────────── */

.workspace-tree__create-dialog {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-xs) var(--usx-spacing-md);
  border-top: 1px solid var(--usx-color-border);
  background-color: var(--usx-color-surface);
  flex-shrink: 0;
}

.workspace-tree__create-input {
  flex: 1;
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border: 1px solid var(--usx-color-primary);
  border-radius: var(--usx-radius-sm);
  background-color: var(--usx-color-background);
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-sm);
  font-family: var(--usx-font-family-sans);
  outline: none;
}
</style>

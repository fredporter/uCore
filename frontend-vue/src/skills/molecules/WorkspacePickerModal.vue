<template>
  <Teleport to="body">
    <div class="ws-picker-overlay" @click.self="emit('close')">
      <div class="ws-picker" role="dialog" aria-modal="true">
        <div class="ws-picker__header">
          <UIcon name="add_box" class="ws-picker__header-icon" />
          <span class="ws-picker__title">Add Workspace</span>
          <button class="ws-picker__close" title="Close" @click="emit('close')">
            <UIcon name="close" />
          </button>
        </div>

        <p class="ws-picker__hint">
          Browse to an existing vault or folder, then add it as a workspace.
        </p>

        <div class="ws-picker__path">
          <button class="ws-picker__home" title="Home" @click="goHome">
            <UIcon name="home" />
          </button>
          <span class="ws-picker__current">{{ currentPath || "—" }}</span>
        </div>

        <input
          v-model="typedPath"
          class="ws-picker__input"
          placeholder="Or type a path…"
          @keydown.enter="openTyped"
        />

        <div class="ws-picker__dirs">
          <button
            v-if="parentPath"
            class="ws-picker__dir ws-picker__dir--up"
            @click="goUp"
          >
            <UIcon name="arrow_upward" /> ..
          </button>
          <button
            v-for="dir in dirs"
            :key="dir"
            class="ws-picker__dir"
            @click="openDir(dir)"
          >
            <UIcon name="folder" /> {{ dir }}
          </button>
          <div v-if="dirs.length === 0 && !parentPath" class="ws-picker__empty">
            No subfolders
          </div>
        </div>

        <div class="ws-picker__footer">
          <button class="ws-picker__btn" @click="emit('close')">Cancel</button>
          <button
            class="ws-picker__btn ws-picker__btn--primary"
            :disabled="adding || !currentPath"
            @click="addCurrent"
          >
            {{ adding ? "Adding…" : "Add this folder" }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
/**
 * @component WorkspacePickerModal
 * @description Folder browser for adding an existing vault/folder as a
 * sidebar workspace. Browses the local filesystem via the library browse API.
 * @category molecules
 * @emits {void} close - Close the picker
 * @emits {object} added - Workspace added { name, path, source }
 */
import { ref, onMounted } from "vue";
import UIcon from "../atoms/UIcon.vue";
import { ucoreApi } from "../../api/client";

const emit = defineEmits<{
  close: [];
  added: [workspace: { name: string; path: string; source: string }];
}>();

const currentPath = ref("");
const parentPath = ref<string | null>(null);
const dirs = ref<string[]>([]);
const typedPath = ref("");
const adding = ref(false);
const error = ref("");

async function load(path = "") {
  try {
    const res = await ucoreApi.library.browse(path);
    if (res.ok && res.data) {
      currentPath.value = String((res.data as any).path || "");
      parentPath.value = (res.data as any).parent || null;
      dirs.value = (res.data as any).dirs || [];
      error.value = "";
    }
  } catch (e: any) {
    error.value = e?.message || "Failed to browse";
  }
}

function goHome() {
  load("");
}

function goUp() {
  if (parentPath.value) load(parentPath.value);
}

function openDir(name: string) {
  load(`${currentPath.value}/${name}`);
}

function openTyped() {
  const p = typedPath.value.trim();
  if (p) load(p);
}

async function addCurrent() {
  if (!currentPath.value || adding.value) return;
  adding.value = true;
  error.value = "";
  try {
    const res = await ucoreApi.library.addWorkspace({ path: currentPath.value });
    if (!res.ok) {
      throw new Error((res.data as any)?.error || `HTTP ${res.status}`);
    }
    emit("added", {
      name: String((res.data as any).name || ""),
      path: String((res.data as any).path || currentPath.value),
      source: String((res.data as any).source || ""),
    });
    emit("close");
  } catch (e: any) {
    error.value = e?.message || "Add failed";
  } finally {
    adding.value = false;
  }
}

onMounted(() => {
  load("");
});
</script>

<style scoped>
.ws-picker-overlay {
  position: fixed;
  inset: 0;
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: color-mix(in srgb, var(--usx-color-background) 60%, transparent);
  backdrop-filter: blur(2px);
  padding: var(--usx-spacing-md);
}

.ws-picker {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
  width: min(420px, 100%);
  background: var(--usx-color-surface);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-lg);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
  padding: var(--usx-spacing-lg);
}

.ws-picker__header {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
}

.ws-picker__header-icon {
  color: var(--usx-color-primary);
  font-size: var(--usx-font-size-xl);
}

.ws-picker__title {
  flex: 1;
  font-size: var(--usx-font-size-lg);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface);
}

.ws-picker__close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: var(--usx-control-size-sm);
  height: var(--usx-control-size-sm);
  min-height: 0;
  padding: 0;
  border: none;
  background: transparent;
  border-radius: var(--usx-radius-sm);
  color: var(--usx-color-on-surface-muted);
  cursor: pointer;
  font-size: var(--usx-font-size-base);
}

.ws-picker__close:hover {
  background-color: var(--usx-color-border);
  color: var(--usx-color-on-surface);
}

.ws-picker__hint {
  margin: 0;
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
}

.ws-picker__path {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: var(--usx-color-background);
}

.ws-picker__home {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  min-height: 0;
  padding: 0;
  border: none;
  background: transparent;
  border-radius: var(--usx-radius-sm);
  color: var(--usx-color-on-surface-muted);
  cursor: pointer;
  font-size: 16px;
  flex-shrink: 0;
}

.ws-picker__home:hover {
  color: var(--usx-color-primary);
  background: color-mix(in srgb, var(--usx-color-primary) 10%, transparent);
}

.ws-picker__current {
  font-size: var(--usx-font-size-sm);
  font-family: var(--usx-font-family-mono);
  color: var(--usx-color-on-surface);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ws-picker__input {
  min-height: var(--usx-control-size-sm);
  padding: 0 var(--usx-spacing-sm);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: var(--usx-color-background);
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-sm);
  font-family: var(--usx-font-family-sans);
}

.ws-picker__input:focus {
  outline: none;
  border-color: var(--usx-color-primary);
}

.ws-picker__dirs {
  display: flex;
  flex-direction: column;
  gap: 2px;
  max-height: 240px;
  overflow-y: auto;
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  padding: var(--usx-spacing-xs);
  background: var(--usx-color-background);
}

.ws-picker__dir {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border: none;
  background: transparent;
  border-radius: var(--usx-radius-sm);
  cursor: pointer;
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-sm);
  font-family: var(--usx-font-family-sans);
  text-align: left;
}

.ws-picker__dir:hover {
  background: color-mix(in srgb, var(--usx-color-primary) 8%, transparent);
}

.ws-picker__dir--up {
  color: var(--usx-color-on-surface-muted);
}

.ws-picker__empty {
  padding: var(--usx-spacing-md);
  text-align: center;
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
}

.ws-picker__error {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-danger);
}

.ws-picker__footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--usx-spacing-sm);
}

.ws-picker__btn {
  min-height: var(--usx-touch-min-sm);
  padding: 0 var(--usx-spacing-md);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-sm);
  font-family: var(--usx-font-family-sans);
  font-weight: var(--usx-font-weight-medium);
  cursor: pointer;
}

.ws-picker__btn:hover {
  background: var(--usx-color-surface-variant);
}

.ws-picker__btn--primary {
  background: var(--usx-color-primary);
  border-color: var(--usx-color-primary);
  color: var(--usx-color-on-primary);
}

.ws-picker__btn--primary:hover {
  background: var(--usx-color-primary-hover);
}

.ws-picker__btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
</style>

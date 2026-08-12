<template>
  <div class="app-shell" :class="{ 'sidebar-open': shell.sidebarOpen }">
    <GlobalToolbar
      :chat-mode="shell.chatMode"
      :sidebar-open="shell.sidebarOpen"
      @toggle-chat="shell.toggleChat"
      @toggle-sidebar="handleGlobalSidebarToggle"
    />
    <div v-if="runtimeWarning" class="app-runtime-warning" role="status">
      <div class="app-runtime-warning__message">{{ runtimeWarning }}</div>
      <div class="app-runtime-warning__actions">
        <button class="app-runtime-warning__btn" @click="reloadPage">
          Reload
        </button>
        <button class="app-runtime-warning__btn" @click="dismissRuntimeWarning">
          Dismiss
        </button>
      </div>
    </div>
    <div
      class="app-body"
      :class="{
        'app-body--tabs-first':
          shell.sidebarOpen && shell.tabOrientation === 'vertical',
        'app-body--tabs-top':
          shell.sidebarOpen && shell.tabOrientation === 'horizontal',
      }"
    >
      <aside v-if="shell.sidebarOpen" class="app-sidebar">
        <FilepickerSidebar
          @file-select="handleFileSelect"
          @new-file="handleNewFile"
        />
      </aside>
      <main class="app-main">
        <router-view />
      </main>
    </div>
    <!-- Snackbar Host -->
    <SnackbarHost />
    <!-- Overlay Layer: chat bubble, toasts, alerts, popups, stories -->
    <OverlayLayer />
  </div>
</template>

<script setup lang="ts">
/**
 * @component AppShell
 * @description Root layout — toolbar + sidebar + router-view + snackbar + overlay.
 * Replaces RootLayout + SurfaceShellContext from React.
 * @category layouts
 */
import { onBeforeUnmount, onMounted, ref } from "vue";
import { useShellStore } from "../stores/shell";
import { useSettingsStore } from "../stores/settings";
import { useWorkflowStore } from "../stores/workflow";
import { useRouter, useRoute } from "vue-router";
import GlobalToolbar from "../skills/organisms/GlobalToolbar.vue";
import FilepickerSidebar from "../skills/molecules/FilepickerSidebar.vue";
import SnackbarHost from "../skills/molecules/SnackbarHost.vue";
import OverlayLayer from "../skills/organisms/OverlayLayer.vue";
import { ucoreApi } from "../api/client";
import type { FileEntry } from "../types/filepicker";

const shell = useShellStore();
const workflow = useWorkflowStore();
const router = useRouter();
const route = useRoute();
const runtimeWarning = ref("");
const RUNTIME_WARNING_KEY = "ucore.runtime.warning";

// Initialize settings store to apply persisted theme (dark mode default)
useSettingsStore();

function syncRuntimeWarningFromSession() {
  if (typeof window === "undefined") return;
  runtimeWarning.value = window.sessionStorage.getItem(RUNTIME_WARNING_KEY) || "";
}

function onRuntimeWarningEvent(event: Event) {
  const detail = (event as CustomEvent<{ message?: string }>).detail;
  runtimeWarning.value = String(detail?.message || "").trim();
}

function dismissRuntimeWarning() {
  runtimeWarning.value = "";
  if (typeof window !== "undefined") {
    window.sessionStorage.removeItem(RUNTIME_WARNING_KEY);
  }
}

function reloadPage() {
  window.location.reload();
}

onMounted(() => {
  syncRuntimeWarningFromSession();
  if (typeof window !== "undefined") {
    window.addEventListener("ucore:runtime-warning", onRuntimeWarningEvent as EventListener);
  }
});

onBeforeUnmount(() => {
  if (typeof window !== "undefined") {
    window.removeEventListener("ucore:runtime-warning", onRuntimeWarningEvent as EventListener);
  }
});

function handleGlobalSidebarToggle() {
  if (route.path === "/developer") {
    shell.toggleDeveloperSidebar();
    return;
  }
  shell.toggleSidebar();
}

async function handleFileSelect(file: FileEntry) {
  let content = file.preview || "";
  try {
    const res = await ucoreApi.library.file(file.path);
    if (res.ok && (res.data as any)?.content !== undefined) {
      content = String((res.data as any).content || "");
    }
  } catch {
    // Fall back to indexed preview content.
  }

  workflow.selectFile({
    id: file.id || file.path,
    path: file.path,
    filename: file.filename,
    extension: file.extension,
    binder: file.binder || "Sandbox",
    content,
    readOnly: Boolean(file.is_readonly),
  });
  await router.push({ path: "/workflow", query: { tab: "editor" } });
}

async function handleNewFile(binderId: string) {
  const binder = (binderId || "user").trim() || "user";
  const titleInput = window.prompt(
    "New markdown document title",
    "Untitled Note",
  );
  if (titleInput === null) {
    return;
  }
  const title = titleInput.trim() || "Untitled Note";
  const safeStem =
    title
      .replace(/[^a-zA-Z0-9._ -]+/g, "-")
      .replace(/\s+/g, " ")
      .trim() || "untitled-note";

  const initialContent = `# ${title}\n\n`;
  const create = await ucoreApi.userWorkflow.importMarkdown({
    content: initialContent,
    source_format: "markdown",
    title,
    binder,
    vault_layer: "user",
    relative_dir: ".",
    filename: `${safeStem}.md`,
    metadata: {
      imported_from: "filepicker.new-file",
    },
  });

  if (!create.ok || !(create.data as any)?.path) {
    window.alert("Failed to create file in vault binder.");
    return;
  }

  const path = String((create.data as any).path);
  const filename = path.split("/").pop() || `${title}.md`;
  let content = initialContent;
  try {
    const fileRes = await ucoreApi.library.file(path);
    if (fileRes.ok && (fileRes.data as any)?.content !== undefined) {
      content = String((fileRes.data as any).content || initialContent);
    }
  } catch {
    // Keep initial content fallback when file API is unavailable.
  }

  workflow.selectFile({
    id: path,
    path,
    filename,
    extension: "md",
    binder,
    content,
    readOnly: false,
  });
  await router.push({ path: "/workflow", query: { tab: "editor" } });
}
</script>

<style scoped>
.app-shell {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  margin: 0;
  padding: 0;
}

.app-body {
  display: flex;
  flex: 1;
  overflow: hidden;
  min-height: 0;
}

.app-runtime-warning {
  position: fixed;
  top: calc(var(--usx-toolbar-height) + var(--usx-spacing-md));
  right: var(--usx-spacing-md);
  z-index: var(--usx-z-notification);
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
  flex-direction: column;
  gap: var(--usx-spacing-md);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  max-width: min(64ch, calc(100vw - (var(--usx-spacing-md) * 2)));
  width: max-content;
  border: var(--usx-border-width) solid var(--usx-color-warning);
  border-radius: var(--usx-radius-md);
  box-shadow: 0 var(--usx-spacing-xs) var(--usx-spacing-lg) color-mix(in srgb, var(--usx-color-on-surface) 18%, transparent);
  background: color-mix(in srgb, var(--usx-color-warning) 16%, transparent);
}

.app-runtime-warning__message {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface);
  line-height: var(--usx-line-height-normal);
  max-width: 56ch;
}

.app-runtime-warning__actions {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  align-self: flex-end;
}

.app-runtime-warning__btn {
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-xs);
  cursor: pointer;
}

.app-runtime-warning__btn:hover {
  border-color: var(--usx-color-warning);
}

@media (max-width: 768px) {
  .app-runtime-warning {
    left: var(--usx-spacing-sm);
    right: var(--usx-spacing-sm);
    top: calc(var(--usx-toolbar-height) + var(--usx-spacing-sm));
    width: auto;
    max-width: none;
  }

  .app-runtime-warning__actions {
    align-self: stretch;
    justify-content: flex-end;
  }
}

.app-sidebar {
  width: var(--usx-sidebar-width);
  overflow-y: auto;
  overflow-x: hidden;
  flex-shrink: 0;
  background: var(--usx-color-surface);
  border-right: var(--usx-border-width) solid var(--usx-color-border);
}

.app-main {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  box-sizing: border-box;
  padding: 0;
  background: var(--usx-color-background);
  min-height: 0;
}

/* ─── Vertical tab layout: tabs become the first column ──────────
   When the surface tab nav is in sidebar (vertical) mode AND the
   filepicker sidebar is open, hoist the surface root so the vertical
   tab nav renders as the leftmost column — before the Filepicker.
   Without this the Filepicker would stay in the first column. */
.app-body--tabs-first :deep(.app-main),
.app-body--tabs-first :deep(.surface),
.app-body--tabs-first :deep(.documentation-surface) {
  display: contents;
}

.app-body--tabs-first .app-sidebar {
  order: 2;
}

.app-body--tabs-first :deep(.surface-tab-nav) {
  order: 1;
}

.app-body--tabs-first :deep(.surface__content),
.app-body--tabs-first :deep(.surface__body),
.app-body--tabs-first :deep(.documentation-content-inner) {
  order: 3;
  flex: 1;
  min-width: 0;
  min-height: 0;
  background: var(--usx-color-background);
}

/* ─── Horizontal tab layout: tabs row on top of the vault sidebar ──
   ORDER IS: Tabs, then Vault. When the surface tab nav is a top bar
   (horizontal) AND the filepicker sidebar is open, hoist the surface
   root into a grid so the tab row spans the full width ABOVE the vault
   sidebar, with content to the right of the vault. */
.app-body--tabs-top {
  display: grid;
  grid-template-columns: auto 1fr;
  grid-template-rows: auto 1fr;
  grid-template-areas:
    "tabs tabs"
    "vault content";
}

.app-body--tabs-top :deep(.app-main),
.app-body--tabs-top :deep(.surface),
.app-body--tabs-top :deep(.documentation-surface) {
  display: contents;
}

.app-body--tabs-top .app-sidebar {
  grid-area: vault;
  min-height: 0;
}

.app-body--tabs-top :deep(.surface-tab-nav) {
  grid-area: tabs;
  width: 100%;
  min-height: 0;
}

.app-body--tabs-top :deep(.surface__content),
.app-body--tabs-top :deep(.surface__body),
.app-body--tabs-top :deep(.documentation-content-inner) {
  grid-area: content;
  min-width: 0;
  min-height: 0;
  overflow-y: auto;
  background: var(--usx-color-background);
}
</style>

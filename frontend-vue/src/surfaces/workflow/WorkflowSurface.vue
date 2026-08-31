<template>
  <div
    class="surface"
    :class="{
      'surface--tab-nav-vertical': shell.tabOrientation === 'vertical',
    }"
  >
    <SurfaceTabNav
      v-model="wf.activeTab"
      :tabs="WORKFLOW_TABS"
      :orientation="shell.tabOrientation"
      @toggle-orientation="shell.toggleTabOrientation()"
    />
    <!-- Content area -->
    <div class="surface__content">
      <CapabilityRepairPanel
        v-if="blockedRepairs.length > 0"
        :items="blockedRepairs"
        @retry="onRetryPreflight"
      />

      <div
        class="workflow-layout"
        :class="{ 'workflow-layout--editor-tab': wf.activeTab === 'editor' }"
      >
        <!-- Left/Main panel: the active tab content -->
        <div v-if="wf.activeTab !== 'editor'" class="workflow-panel">
          <MissionControlPanel v-if="wf.activeTab === 'mission-control'" />
          <TasksPanel v-else-if="wf.activeTab === 'tasks'" />
          <AutomationPanel v-else-if="wf.activeTab === 'automation'" />
          <FeedsPanel v-else-if="wf.activeTab === 'feeds'" />
          <PublishPanel v-else-if="wf.activeTab === 'publish'" />
        </div>

        <!-- Editor tab: full-width document workspace -->
        <div
          v-if="wf.activeTab === 'editor'"
          class="workflow-panel workflow-panel--editor"
        >
          <aside class="workflow-workspace-tree">
            <WorkspaceTree />
          </aside>
          <EditorPanel
            v-if="activeEditorItem"
            :content="editorContent"
            :title="editorTitle"
            :read-only="editorReadOnly"
            :edit-mode="wf.editorMode"
            @update:content="onEditorContentUpdate"
            @update:edit-mode="onEditorModeUpdate"
            @save="onEditorSave"
            @close="wf.closeEditor()"
          />
          <div v-else class="wf-editor-empty">
            <UIcon name="diamond" />
            <p>
              Select a file from the User Vault sidebar or a task from Tasks.
            </p>
            <div class="wf-editor-empty__actions">
              <UButton
                size="sm"
                variant="primary"
                @click="shell.toggleSidebar()"
              >
                Open File Browser
              </UButton>
              <UButton
                size="sm"
                variant="secondary"
                @click="wf.setTab('tasks')"
              >
                Go to Tasks
              </UButton>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @component WorkflowSurface
 * @description Workflow surface with mission control, kanban tasks, binder cross-reference,
 * and workflow publish/run management. Uses USX canonical .surface / .surface__tabs / .surface__content classes.
 *
 * Editor layout:
 *   - No editor: [Main Panel 100%]
 *   - Preview only: [Main Panel 2/3] | [Preview 1/3]
 *   - Both panes:  [Main Panel 1/3] | [Edit 1/3 | Preview 1/3]
 *
 * @category surfaces
 * @usage Routed at '/workflow?tab=mission-control'
 */
import { computed, defineAsyncComponent, onMounted, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useShellStore } from "../../stores/shell";
import { useWorkflowStore, WORKFLOW_TABS } from "../../stores/workflow";
import { useWorkspaceStore } from "../../stores/workspace";
import type { WorkflowTab } from "../../stores/workflow";
import { getEditorSurface } from "../../composables/useEditorSurface";
import SurfaceTabNav from "../../skills/molecules/SurfaceTabNav.vue";
import CapabilityRepairPanel from "../../skills/molecules/CapabilityRepairPanel.vue";
import MissionControlPanel from "./panels/MissionControlPanel.vue";
const MissionsPanel = defineAsyncComponent(
  () => import("./panels/MissionsPanel.vue"),
);
const AutomationPanel = defineAsyncComponent(
  () => import("./panels/AutomationPanel.vue"),
);
const FeedsPanel = defineAsyncComponent(
  () => import("./panels/FeedsPanel.vue"),
);
const TasksPanel = defineAsyncComponent(
  () => import("./panels/TasksPanel.vue"),
);
const PublishPanel = defineAsyncComponent(
  () => import("./panels/PublishPanel.vue"),
);
import { EditorPanel } from "../../skills";
import UIcon from "../../skills/atoms/UIcon.vue";
import UButton from "../../skills/atoms/UButton.vue";
import WorkspaceTree from "../../skills/molecules/editor/WorkspaceTree.vue";

const shell = useShellStore();
const wf = useWorkflowStore();
const workspace = useWorkspaceStore();
const editorSurface = getEditorSurface();
const route = useRoute();
const router = useRouter();

const VALID_WORKFLOW_TABS = new Set(WORKFLOW_TABS.map((t) => t.id));

function ensureEditorDocument() {
  if (wf.activeTab === "editor") {
    wf.ensureDefaultEditorFile();
  }
}

function asWorkflowTab(tab: string): WorkflowTab | null {
  return VALID_WORKFLOW_TABS.has(tab as WorkflowTab)
    ? (tab as WorkflowTab)
    : null;
}

onMounted(() => {
  void workspace.loadTree();
  const routeTab = String(route.query.tab || "").trim();
  const safeTab = asWorkflowTab(routeTab);
  if (safeTab) {
    wf.setTab(safeTab);
  } else {
    router.replace({
      path: "/workflow",
      query: { ...route.query, tab: wf.activeTab },
    });
  }

  ensureEditorDocument();

  void wf.fetchAll();
});

watch(
  () => route.query.tab,
  (value) => {
    const routeTab = String(value || "").trim();
    const safeTab = asWorkflowTab(routeTab);
    if (!safeTab) return;
    if (wf.activeTab !== routeTab) {
      wf.setTab(safeTab);
    }
    if (safeTab === "editor") {
      wf.ensureDefaultEditorFile();
    }
  },
);

watch(
  () => wf.activeTab,
  (tab, prev) => {
    if (tab === "editor") {
      wf.ensureDefaultEditorFile();
    }
    // Close any lingering editor when leaving the Tasks tab
    if (prev === "tasks" && tab !== "tasks") {
      wf.closeEditor();
    }
    const current = String(route.query.tab || "");
    if (current === tab) return;
    router.replace({
      path: "/workflow",
      query: { ...route.query, tab },
    });
  },
);

watch(
  () => [wf.activeTab, wf.selectedTask?.id || "", wf.selectedFile?.id || ""],
  ([tab, taskId, fileId]) => {
    if (tab !== "editor") return;
    if (!taskId && !fileId) {
      wf.ensureDefaultEditorFile();
    }
  },
);

function onEditorContentUpdate(value: string) {
  if (sharedEditorFile.value) {
    editorSurface.updateContent(value);
  } else {
    wf.updateEditorContent(value);
  }
}

async function onEditorSave(value: string) {
  if (sharedEditorFile.value) {
    editorSurface.updateContent(value);
    await workspace.saveFile(sharedEditorFile.value.path, value);
    return;
  }
  wf.updateEditorContent(value);
  const itemId = wf.selectedTask?.id || wf.selectedFile?.path;
  console.log("[Workflow] Editor saved:", itemId);
}

function onEditorModeUpdate(mode: "prose" | "code") {
  wf.setEditorMode(mode);
}

const sharedEditorFile = computed(
  () => editorSurface.currentFile.value ?? null,
);
const activeWorkflowFile = computed(
  () => sharedEditorFile.value || wf.selectedFile,
);
const activeEditorTask = computed(() =>
  sharedEditorFile.value ? null : wf.selectedTask || null,
);
const activeEditorItem = computed(
  () => activeEditorTask.value || activeWorkflowFile.value,
);
const editorTitle = computed(
  () =>
    activeEditorTask.value?.title ||
    activeWorkflowFile.value?.filename ||
    editorSurface.title.value ||
    "Untitled",
);
const editorContent = computed(
  () =>
    activeEditorTask.value?.description ||
    activeWorkflowFile.value?.content ||
    "",
);
const editorReadOnly = computed(() =>
  Boolean(activeWorkflowFile.value?.readOnly),
);

/**
 * Dynamic column class based on edit pane visibility:
 *   - Edit pane open: wider column (50% for both panes stacked vertically)
 *   - Edit pane hidden: narrower column (50% — preview fills it)
 */
// Markdown editor now full-width; no dynamic layout needed

const blockedRepairs = computed(() => {
  return Object.values(wf.capabilityRepairs || {}).filter(
    (item) => !item.ready,
  );
});

function onRetryPreflight() {
  void wf.fetchAll();
}
</script>

<style scoped>
/* ─── Layout ──────────────────────────────────────────────────────── */
.workflow-layout {
  display: flex;
  flex-direction: row;
  height: 100%;
  gap: var(--usx-spacing-md);
}

.workflow-layout--editor-tab {
  gap: 0;
}

/* ─── Main Panel — fill full height ──────────────────────────── */
.workflow-panel {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

.workflow-panel > * {
  flex: 1;
  min-height: 0;
}

/* Editor tab is full-width — hoist the editor to fill the layout
   directly, removing the intermediate box (compact, no border layer). */
.workflow-panel--editor {
  display: contents;
}

.workflow-layout--editor-tab > .editor-panel {
  flex: 1;
  min-width: 0;
  min-height: 0;
}

.workflow-workspace-tree {
  width: min(18rem, 28vw);
  min-width: 12rem;
  flex-shrink: 0;
  min-height: 0;
}

@media (max-width: 767px) {
  .workflow-workspace-tree {
    width: 11rem;
    min-width: 9rem;
  }
}

/* ─── Editor Column — right sidebar, full height ──────────────── */
/* Editor column: Markdown takes 1/3 width as sidecar */
.workflow-editor {
  flex-shrink: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: var(--usx-color-background);
  width: 33.33%;
  min-width: 22ch;
}

/* ─── Empty editor state ──────────────────────────────────────────── */
.wf-editor-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--usx-spacing-md);
  padding: var(--usx-spacing-2xl);
  color: var(--usx-color-on-surface-muted);
  text-align: center;
}

.wf-editor-empty__actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--usx-spacing-sm);
  flex-wrap: wrap;
}
</style>

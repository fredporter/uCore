<template>
  <div
    class="surface"
    :class="{
      'surface--tab-nav-vertical': shell.tabOrientation === 'vertical',
    }"
  >
    <SurfaceTabNav
      :model-value="navigationTab"
      @update:model-value="wf.setTab($event as WorkflowTab)"
      :tabs="navigationTabs"
      :orientation="shell.tabOrientation"
      @toggle-orientation="shell.toggleTabOrientation()"
    />
    <div class="surface__content workflow-content">
      <Teleport v-if="wf.activeTab === 'editor' && activeEditorItem" defer
        to="#workflow-editor-sidebar-context" :key="String(shell.sidebarOpen)" :disabled="!shell.sidebarOpen">
      <div class="workflow-context" :class="{ 'workflow-context--compact': !shell.sidebarOpen }" aria-label="Current item">
        <button class="usx-btn" aria-label="Open document index" title="Open document index"
          @click="shell.setSidebarMode('vault'); shell.setSidebarOpen(true)"><UIcon name="folder_open" aria-hidden="true" /></button>
        <button v-if="wf.activeBinderId" class="usx-btn" aria-label="Open Binder" title="Open Binder" @click="wf.binders.some(binder => binder.id === wf.activeBinderId) ? wf.showBinder(wf.activeBinderId) : wf.showList('', wf.activeBinderId)"><UIcon name="book" aria-hidden="true" /><span class="workflow-context__label">{{ wf.binders.find(b => b.id === wf.activeBinderId)?.title || wf.activeBinderId }}</span></button>
        <button class="usx-btn" aria-label="Tasks" title="Tasks" @click="wf.showList(wf.activeList, wf.activeBinderId)"><UIcon name="list" aria-hidden="true" /><span class="workflow-context__label">Tasks</span></button>
        <strong v-if="activeEditorTask" :title="editorTitle">{{ editorTitle }}</strong><small v-if="wf.hasEditorDraft">Unsaved</small>
        <span class="workflow-context__actions" v-if="activeEditorTask">
          <span>{{ contextPosition + 1 }} of {{ wf.relatedTasks.length }} · {{ wf.relatedTasks.filter(task => task.status === 'completed').length }} done</span>
          <button class="usx-btn" aria-label="Previous task" :disabled="contextPosition <= 0" @click="navigateTask(-1)"><UIcon name="chevron_left" /></button>
          <button class="usx-btn" aria-label="Next task" :disabled="contextPosition < 0 || contextPosition >= wf.relatedTasks.length - 1" @click="navigateTask(1)"><UIcon name="chevron_right" /></button>
          <button class="usx-btn" :disabled="saving" :title="activeEditorTask.status === 'completed' ? 'Reopen' : 'Mark done'"
            :aria-label="activeEditorTask.status === 'completed' ? 'Reopen' : 'Mark done'" @click="completeTask()">
            <UIcon :name="activeEditorTask.status === 'completed' ? 'undo' : 'check'" aria-hidden="true" />
          </button>
          <button class="usx-btn" :disabled="saving" title="Done and next" aria-label="Done and next" @click="completeTask(true)"><UIcon name="playlist_add_check" aria-hidden="true" /></button>
        </span>
      </div>
      </Teleport>
      <BrowserUISurface
        v-if="wf.activeTab === 'research'"
        :key="wf.activeBinderId"
        :binder-id="wf.activeBinderId || undefined"
        embedded
        class="workflow-research"
      >
        <CapabilityRepairPanel
          v-if="blockedRepairs.length > 0"
          :items="blockedRepairs"
          :busy="wf.recheckingCapabilities"
          @retry="onRetryPreflight"
        />
      </BrowserUISurface>
      <div
        v-else
        class="workflow-layout"
        :class="{ 'workflow-layout--editor-tab': wf.activeTab === 'editor' }"
      >
        <form v-if="saveAsOpen" class="surface__panel" @submit.prevent="saveDraftAsFile">
          <label>File name <input v-model="saveAsName" required aria-label="File name" /></label>
          <UButton type="submit" :disabled="saving">Save to files</UButton>
          <UButton type="button" variant="secondary" :disabled="saving" @click="saveAsOpen = false">Cancel</UButton>
        </form>
        <p v-if="saveMessage" :role="saveFailed ? 'alert' : 'status'">{{ saveMessage }}</p>
        <CapabilityRepairPanel
          v-if="blockedRepairs.length > 0"
          :items="blockedRepairs"
          :busy="wf.recheckingCapabilities"
          @retry="onRetryPreflight"
        />

        <!-- Left/Main panel: the active tab content -->
        <nav v-if="sectionViews.length" class="workflow-section-nav" :aria-label="navigationTab === 'tasks' ? 'List views' : 'Mission views'">
          <button v-for="view in sectionViews" :key="view.id" type="button" class="usx-btn"
            :aria-current="wf.activeTab === view.id ? 'page' : undefined" @click="wf.setTab(view.id)">
            <UIcon :name="view.icon" aria-hidden="true" />{{ view.label }}
          </button>
        </nav>
        <div v-if="wf.activeTab !== 'editor'" class="workflow-panel">
          <WorkflowDashboardPanel v-if="wf.activeTab === 'mission-control'" />
          <TasksPanel v-else-if="wf.activeTab === 'tasks'" />
          <ConnectionsPanel v-else-if="wf.activeTab === 'contacts'" collection-only initial-kind="contacts" />
          <ConnectionsPanel v-else-if="wf.activeTab === 'notes'" collection-only initial-kind="notes" />
          <FeedsPanel v-else-if="wf.activeTab === 'feeds'" />
          <WorkflowQueuePanel v-else-if="wf.activeTab === 'queue'" class="workflow-panel__queue" />
          <NotebookBinderPanel v-else-if="wf.activeTab === 'binder'" />
          <LocalAssistantPanel v-else-if="wf.activeTab === 'ai'" />
          <WorkflowSkillsPanel v-else-if="wf.activeTab === 'skills'" />
        </div>

        <!-- Editor tab: full-width document workspace -->
        <div
          v-if="wf.activeTab === 'editor'"
          class="workflow-panel workflow-panel--editor"
          @click="openBinderNotebookLink"
        >
          <EditorPanel
            v-if="activeEditorItem"
            :content="editorContent"
            :title="editorTitle"
            :document-path="activeWorkflowFile?.path"
            :read-only="editorReadOnly"
            :can-edit-copy="Boolean(editorReadOnly && activeWorkflowFile?.extension === 'md' && !wf.binderDocument)"
            :start-in-edit="activeWorkflowFile?.path.startsWith('virtual/copy/')"
            @edit-copy="editVaultCopy"
            :edit-mode="wf.editorMode"
            @update:content="onEditorContentUpdate"
            @update:edit-mode="onEditorModeUpdate"
            @save="onEditorSave"
            @publish="openPublishing"
            @close="returnToContext"
          />
          <Transition name="workflow-publish">
            <aside v-if="publishOpen && activeEditorItem" class="workflow-publish-drawer">
              <header class="workflow-publish-drawer__header">
                <div>
                  <strong>Publish</strong>
                  <span>{{ editorTitle }}</span>
                </div>
                <button class="usx-btn" aria-label="Close publishing" @click="publishOpen = false"><UIcon name="close" :size="20" /></button>
              </header>
              <PublishPanel :source-title="editorTitle" :source-content="editorContent" embedded />
            </aside>
          </Transition>
          <div v-if="!activeEditorItem" class="wf-editor-empty">
            <UIcon name="diamond" :size="48" aria-hidden="true" />
            <p>
              Open a task or binder draft to continue, or choose a file from the sidebar.
            </p>
            <div class="wf-editor-empty__actions">
              <UButton
                size="sm"
                variant="primary"
                @click="shell.setSidebarOpen(true)"
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
import { computed, defineAsyncComponent, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useShellStore } from "../../stores/shell";
import ConnectionsPanel from "../system/ConnectionsPanel.vue";
import FeedsPanel from "./panels/FeedsPanel.vue";
import WorkflowQueuePanel from "./panels/WorkflowQueuePanel.vue";
import BrowserUISurface from "../browserui/BrowserUISurface.vue";
import { useWorkflowStore, WORKFLOW_TABS } from "../../stores/workflow";
import { UCORE_BASE } from "../../api/base";
import { useWorkspaceStore } from "../../stores/workspace";
import type { WorkflowTab } from "../../stores/workflow";
import { getEditorSurface } from "../../composables/useEditorSurface";
import SurfaceTabNav from "../../skills/molecules/SurfaceTabNav.vue";
import CapabilityRepairPanel from "../../skills/molecules/CapabilityRepairPanel.vue";
import WorkflowDashboardPanel from "./panels/WorkflowDashboardPanel.vue";
const TasksPanel = defineAsyncComponent(
  () => import("./panels/TasksPanel.vue"),
);
const PublishPanel = defineAsyncComponent(
  () => import("./panels/PublishPanel.vue"),
);
const LocalAssistantPanel = defineAsyncComponent(() => import("../snackbar/panels/LocalAssistantPanel.vue"));
const WorkflowSkillsPanel = defineAsyncComponent(() => import("./panels/WorkflowSkillsPanel.vue"));
const NotebookBinderPanel = defineAsyncComponent(
  () => import("./panels/NotebookBinderPanel.vue"),
);
import { EditorPanel } from "../../skills";
import UIcon from "../../skills/atoms/UIcon.vue";
import UButton from "../../skills/atoms/UButton.vue";

const shell = useShellStore();
const wf = useWorkflowStore();
const workspace = useWorkspaceStore();
let restoringLocation = true;
const publishOpen = ref(false);

const editorSurface = getEditorSurface();
const route = useRoute();
const router = useRouter();

watch(() => route.query.tab, tab => {
  if (["contacts", "notes"].includes(String(tab))) {
    void router.replace({ path: "/snackbar", query: { tab: String(tab) } });
  }
}, { immediate: true });

const missionViews = [
  { id: "mission-control", label: "Dashboard", icon: "schedule" },
  { id: "binder", label: "Binders", icon: "book" },
] as const;
const listViews = [
  { id: "tasks", label: "Tasks", icon: "check" },
  { id: "feeds", label: "Feeds", icon: "rss_feed" },
  { id: "queue", label: "Queue", icon: "pending_actions" },
] as const;
const navigationTabs = WORKFLOW_TABS
  .filter(tab => tab.id !== "binder" && tab.id !== "queue")
  .map(tab => tab.id === "tasks" ? { ...tab, label: "Lists", icon: "list_alt" } : tab);
const navigationTab = computed(() => {
  if (wf.activeTab === "binder") return "mission-control";
  if (wf.activeTab === "feeds" || wf.activeTab === "queue") return "tasks";
  return wf.activeTab;
});
const sectionViews = computed(() => navigationTab.value === "mission-control" ? missionViews
  : navigationTab.value === "tasks" ? listViews : []);

const VALID_WORKFLOW_TABS = new Set<WorkflowTab>([...WORKFLOW_TABS.map(tab => tab.id), "feeds"]);

function asWorkflowTab(tab: string): WorkflowTab | null {
  return VALID_WORKFLOW_TABS.has(tab as WorkflowTab)
    ? (tab as WorkflowTab)
    : null;
}

function tabFromLocation() {
  const tab = String(route.query.tab || "").trim();
  return asWorkflowTab(tab === "binder" && route.query.view === "research" ? "research" : tab);
}

onMounted(async () => {
  if (["contacts", "notes"].includes(String(route.query.tab))) return;
  const safeTab = tabFromLocation();
  if (safeTab) {
    wf.setTab(safeTab);
  } else {
    router.replace({
      path: "/workflow",
      query: { ...route.query, tab: wf.activeTab },
    });
  }


  wf.activeList = String(route.query.list || "");
  wf.activeBinderId = String(route.query.binder || "");
  wf.activeMissionId = String(route.query.mission || "");
  const selectionAtLoad = wf.selectedTask?.id;
  const fileAtLoad = editorSurface.currentFile.value?.path;
  const taskId = String(route.query.task || "");
  const documentPart = String(route.query.document || "");
  const filePath = String(route.query.file || "");
  await wf.fetchAll();
  if (wf.activeBinderId.toLowerCase() === "sandbox" &&
      !wf.binders.some(binder => binder.id === wf.activeBinderId) &&
      route.query.binder === wf.activeBinderId) {
    await router.replace({ query: { ...route.query, binder: undefined } });
    wf.activeBinderId = "";
  }
  wf.setTaskContext(wf.activeList, wf.activeBinderId);
  if (!wf.missions.some(mission => mission.id === wf.activeMissionId)) wf.activeMissionId = "";
  else if (!route.query.binder) wf.selectMission(wf.activeMissionId);
  try {
    const selectionChanged = wf.selectedTask?.id !== selectionAtLoad || editorSurface.currentFile.value?.path !== fileAtLoad;
    if (selectionChanged) { /* Keep user navigation that happened during hydration. */ }
    else if (taskId) {
      const task = wf.tasks.find(task => task.id === taskId);
      if (task) wf.openTask(task);
    } else if (wf.activeBinderId && ["brief", "draft"].includes(documentPart)) {
      const response = await fetch(`${UCORE_BASE}/api/binder/${encodeURIComponent(wf.activeBinderId)}`, { signal: AbortSignal.timeout(8000) });
      if (!response.ok) throw new Error("Could not restore binder document");
      const { binder } = await response.json();
      wf.openBinderDocument(wf.activeBinderId, `${binder.metadata.title} · ${documentPart}`, binder[documentPart] || "", binder.draft_sha256 || "", documentPart === "brief");
    } else if (filePath && safeTab === "editor") {
      await workspace.selectFile({ id: filePath, path: filePath, name: filePath.split("/").pop() || "Document", type: "file" });
      if (editorSurface.currentFile.value?.path !== filePath) {
        const response = await fetch(`${UCORE_BASE}/api/library/file?path=${encodeURIComponent(filePath)}`, {
          signal: AbortSignal.timeout(8000),
        });
        if (!response.ok) throw new Error("Could not open the indexed document");
        const file = await response.json();
        if (wf.selectedTask?.id === selectionAtLoad && editorSurface.currentFile.value?.path === fileAtLoad) {
          wf.selectFile({ ...file, id: file.path, binder: "", readOnly: true });
        }
      }
    }
  } catch (error) { saveFailed.value = true; saveMessage.value = error instanceof Error ? error.message : "Could not restore item"; }
  restoringLocation = false;
  syncLocation();
});

function syncLocation() {
  if (restoringLocation) return;
  const query = { ...route.query, view: undefined, mission: wf.activeMissionId || undefined, tab: wf.activeTab, list: wf.activeList || undefined, binder: wf.activeBinderId || undefined, task: wf.activeTab === "editor" ? wf.selectedTask?.id : undefined, document: wf.activeTab === "editor" && wf.binderDocument ? (wf.binderDocument.readOnly ? "brief" : "draft") : undefined, file: wf.activeTab === "editor" && !wf.selectedTask && !wf.binderDocument ? editorSurface.currentFile.value?.path : undefined };
  if (["tab", "list", "binder", "mission", "task", "document", "file", "view"].some(key => String(route.query[key] || "") !== String(query[key as keyof typeof query] || ""))) void router.replace({ path: "/workflow", query });
}
watch(() => [wf.activeTab, wf.activeMissionId, wf.activeList, wf.activeBinderId, wf.selectedTask?.id, wf.binderDocument?.path, editorSurface.currentFile.value?.path], syncLocation);
watch(() => route.query.task, value => {
  const task = wf.tasks.find(task => task.id === value);
  if (task && wf.selectedTask?.id !== task.id) wf.openTask(task);
});

watch(
  () => [route.query.tab, route.query.binder, route.query.view, route.query.mission],
  () => {
    const tab = tabFromLocation();
    if (!tab) return;
    const binder = String(route.query.binder || "");
    if (wf.activeBinderId !== binder) wf.setTaskContext(String(route.query.list || ""), binder);
    const mission = String(route.query.mission || "");
    if (mission && wf.missions.some(item => item.id === mission)) wf.activeMissionId = mission;
    if (wf.activeTab !== tab) wf.setTab(tab);
    if (route.query.tab === "binder" && route.query.view === "research") syncLocation();
  },
);

watch(() => [wf.selectedTask?.id, wf.selectedFile?.id, workspace.selectedId], () => { publishOpen.value = false; });


function onEditorContentUpdate(value: string) { wf.updateEditorContent(value); }

const saveAsOpen = ref(false);
const saveAsName = ref("Untitled.md");
const pendingDraft = ref("");
const saving = ref(false);
const saveMessage = ref("");
const saveFailed = ref(false);

function editVaultCopy() {
  const file = activeWorkflowFile.value;
  if (!file?.readOnly) return;
  const path = `virtual/copy/${file.path}`;
  wf.selectFile({ ...file, id: path, path, binder: "", content: editorContent.value, readOnly: false });
  wf.setEditorMode("code");
}

async function onEditorSave(value: string) {
  if (saving.value) return;
  saving.value = true;
  saveFailed.value = false;
  saveMessage.value = "Saving…";
  try {
    if (activeEditorTask.value) {
      await wf.patchTask(activeEditorTask.value.id, { body: value });
    } else if (wf.binderDocument) {
      await wf.saveBinderDocument(value);
    } else if (activeWorkflowFile.value) {
      const file = activeWorkflowFile.value;
      if (file.readOnly) throw new Error("This file is read-only.");
      if (file.path.startsWith("virtual/")) {
        pendingDraft.value = value;
        saveAsName.value = file.filename || "Untitled.md";
        saveAsOpen.value = true;
        saveMessage.value = "";
        return;
      }
      editorSurface.updateContent(value);
      const saved = await workspace.saveFile(file.path, value, sharedEditorFile.value?.version);
      if (!saved) {
        saveMessage.value = workspace.error || "Offline: save queued for reconnection.";
        return;
      }
    } else {
      throw new Error("Open a task or file to save changes.");
    }
    delete wf.editorDrafts[wf.editorKey];
    saveMessage.value = "Saved";
  } catch (error) {
    saveFailed.value = true;
    saveMessage.value = error instanceof Error ? error.message : "Could not save changes.";
  } finally {
    saving.value = false;
  }
}

async function saveDraftAsFile() {
  if (saving.value) return;
  saving.value = true;
  saveFailed.value = false;
  try {
    const file = await workspace.createFile("/Sandbox", saveAsName.value);
    editorSurface.updateContent(pendingDraft.value);
    saveAsOpen.value = false;
    const saved = await workspace.saveFile(file.path, pendingDraft.value);
    saveAsOpen.value = false;
    saveMessage.value = saved ? "Saved" : workspace.error;
  } catch (error) {
    saveFailed.value = true;
    saveMessage.value = error instanceof Error ? error.message : "Could not save changes.";
  } finally {
    saving.value = false;
  }
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
async function openBinderNotebookLink(event: MouseEvent) {
  if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
  const anchor = event.target instanceof Element ? event.target.closest(".md-preview a[href]") : null;
  const href = anchor?.getAttribute("href");
  const source = activeWorkflowFile.value?.path.match(/^((?:\/binders)?\/([^/]+)\/docs\/)[^/]+$/i);
  if (!href || !source || anchor?.hasAttribute("download")) return;
  if (!source[1].toLowerCase().startsWith("/binders/") && !wf.binders.some(binder => binder.id === source[2])) return;
  // Binder imports store sibling Markdown files in docs/. Other links keep their native behavior.
  const relative = href.replace(/^\.\//, "");
  if (!/^[^/:?#\\]+\.md$/i.test(relative)) return;
  let filename: string;
  try { filename = decodeURIComponent(relative); } catch { return; }
  if (!/^[^/:?#\\\x00-\x1f]+\.md$/i.test(filename)) return;
  event.preventDefault();
  try {
    await wf.openVaultDocument(source[1] + filename, filename, source[2]);
  } catch (error) {
    saveFailed.value = true;
    saveMessage.value = error instanceof Error ? error.message : "Could not open the linked Binder document.";
  }
}

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
const editorContent = computed(() => wf.editorDrafts[wf.editorKey] ?? activeEditorTask.value?.description ?? activeWorkflowFile.value?.content ?? "");
const contextPosition = computed(() => wf.relatedTasks.findIndex(task => task.id === activeEditorTask.value?.id));
function navigateTask(offset: number) {
  const task = wf.relatedTasks[contextPosition.value + offset];
  if (task) wf.openTask(task);
}
function openPublishing() {
  if (wf.binderDocument) { wf.binderStage = "publish"; wf.showBinder(wf.activeBinderId); }
  else publishOpen.value = true;
}
function returnToContext() {
  if (wf.binderDocument) wf.showBinder(wf.activeBinderId);
  else wf.showList(wf.activeList, wf.activeBinderId);
}
async function completeTask(advance = false) {
  if (!activeEditorTask.value || saving.value) return;
  const current = activeEditorTask.value;
  const next = wf.relatedTasks.find(task => task.id !== current.id && ["todo", "in-progress", "review"].includes(task.status));
  saving.value = true;
  try {
    await wf.patchTask(current.id, { status: advance || current.status !== "completed" ? "completed" : "todo", ...(wf.hasEditorDraft ? { body: editorContent.value } : {}) });
    if (advance && next) wf.openTask(next);
    else if (advance) wf.showList(wf.activeList, wf.activeBinderId);
    saveMessage.value = "Task updated";
  } catch (error) { saveFailed.value = true; saveMessage.value = error instanceof Error ? error.message : "Could not update task"; }
  finally { saving.value = false; }
}
watch(() => editorSurface.currentFile.value?.path, path => {
  if (!path) return;
  if (wf.binderDocument?.path !== path) wf.binderDocument = null;
  wf.selectedTask = null;
  if (wf.selectedFile?.path !== path) wf.selectedFile = null;
});
watch(() => [wf.selectedTask?.id, wf.selectedFile?.path], () => { saveMessage.value = ""; saveFailed.value = false; });

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
  void wf.retryCapabilityPreflight();
}
</script>

<style scoped>
.workflow-panel :deep(input), .workflow-panel :deep(select), .workflow-panel :deep(textarea) { max-width: 100%; box-sizing: border-box; }

.workflow-content {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
}

.workflow-context { display: flex; flex-wrap: wrap; align-items: center; gap: var(--usx-spacing-xs); padding: var(--usx-spacing-sm); border-bottom: 1px solid var(--usx-color-border); }
.workflow-context strong { min-width: 0; overflow-wrap: anywhere; }
.workflow-context--compact .workflow-context__label { display: none; }
.workflow-context .usx-btn { margin: 0; min-height: 32px; padding: 4px 6px; }
.workflow-context__actions { margin-left: auto; display: flex; flex-wrap: wrap; align-items: center; gap: var(--usx-spacing-xs); }
.workflow-context small { color: var(--usx-color-warning); }

.workflow-research {
  --wf-zen-pad: clamp(12px, 2vw, 20px);
  flex: 1;
  min-width: 0;
  height: auto;
}

/* ─── Layout ──────────────────────────────────────────────────────── */
.workflow-layout {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  gap: var(--usx-spacing-md);
}

.workflow-layout--editor-tab {
  position: relative;
  gap: 0;
}

/* ─── Main Panel — fill full height ──────────────────────────── */
.workflow-section-nav {
  display: flex;
  flex: 0 0 auto;
  flex-wrap: wrap;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
}
.workflow-section-nav .usx-btn {
  margin: 0;
  min-height: 32px;
  padding: 4px 8px;
  border: 0;
  box-shadow: none;
  background: transparent;
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-sm);
}
.workflow-section-nav [aria-current="page"] { background: var(--usx-color-surface-hover); }
.workflow-section-nav [aria-current="page"] { color: var(--usx-color-primary); }

.workflow-panel {
  flex: 1;
  min-width: 0;
  min-height: 0;
  overflow-y: auto;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

.workflow-publish-drawer {
  position: absolute;
  inset: 0 0 0 auto;
  z-index: 35;
  display: flex;
  flex-direction: column;
  width: min(28rem, 92vw);
  min-height: 0;
  border-left: var(--usx-border-width) solid var(--usx-color-border);
  background: var(--usx-color-background);
}

.workflow-panel--editor { position: relative; overflow: hidden; }
.workflow-publish-drawer__header { display: flex; align-items: center; justify-content: space-between; gap: var(--usx-spacing-sm); padding: var(--usx-spacing-md); border-bottom: var(--usx-border-width) solid var(--usx-color-border); }
.workflow-publish-drawer__header > div { display: grid; gap: 2px; min-width: 0; }
.workflow-publish-drawer__header span { overflow: hidden; color: var(--usx-color-on-surface-muted); font-size: var(--usx-font-size-xs); text-overflow: ellipsis; white-space: nowrap; }
.workflow-publish-drawer__header button { display: inline-flex; align-items: center; justify-content: center; width: var(--usx-control-size-sm); height: var(--usx-control-size-sm); min-height: 0; padding: 0; border: 0; background: transparent; color: var(--usx-color-on-surface-muted); }
.workflow-publish-enter-active, .workflow-publish-leave-active { transition: transform 160ms ease; }
.workflow-publish-enter-from, .workflow-publish-leave-to { transform: translateX(100%); }

.workflow-panel > .workflow-panel__queue { flex: 0 0 auto; }

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

<style scoped>
.workflow-context { flex-wrap: nowrap; min-height: 44px; box-sizing: border-box; padding: 4px 8px; overflow: hidden; white-space: nowrap; font-size: var(--usx-font-size-sm); }
.workflow-context strong { flex: 1 1 auto; min-width: 0; overflow: hidden; text-overflow: ellipsis; }
.workflow-context__label, .workflow-context__actions > span { display: none; }
.workflow-context__actions { flex: 0 0 auto; flex-wrap: nowrap; gap: 4px; }
.workflow-context button.usx-btn { display: inline-flex; align-items: center; justify-content: center; flex-shrink: 0; gap: 4px; box-sizing: border-box; height: 32px; min-height: 32px; margin: 0; padding: 0 8px; border: 0; box-shadow: none; background: transparent; font-size: inherit; line-height: 1; }
.workflow-context button.usx-btn:hover { background: var(--usx-color-surface-variant); }
.workflow-context :deep(.u-icon) { width: 20px; height: 20px; font-size: 20px; line-height: 1; }
</style>

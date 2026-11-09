/**
 * @module stores/workflow
 * @description Workflow surface state — tasks, missions, binder, publish, kanban.
 * Wires to backend /api/workflows/*, /api/system/workflow, /api/workflow/tasks,
 * and /api/knowledge/adapter/mission-task-binder endpoints.
 */
import { defineStore } from "pinia";
import { useWorkspaceStore } from "./workspace";
import { ref, computed } from "vue";
import {
  ensureCapabilityReady,
  type CapabilityPreflightResult,
} from "@/api/preflight";
import { getEditorSurface } from "@/composables/useEditorSurface";

export type WorkflowTab =
  | "mission-control"
  | "tasks"
  | "binder"
  | "contacts"
  | "notes"
  | "feeds"
  | "queue"
  | "research"
  | "editor";

export interface WorkflowTask {
  id: string;
  title: string;
  status: string;
  priority: "low" | "medium" | "high";
  board: string;
  tags: string[];
  description: string;
  binder?: string;
  group?: string;
  workspace?: string;
  workflowType?: "user" | "developer" | "system" | "autonomous";
  summary?: string;
  notes?: string;
  assetPaths?: string[];
  steps?: WorkflowStep[];
  completedAt?: string | null;
  action_type?: string;
  action_payload?: Record<string, any>;
  approval_status?: string;
  due?: string;
}

export type WorkflowStepStatus =
  | "todo"
  | "in-progress"
  | "completed"
  | "blocked";

export interface WorkflowStep {
  id: string;
  title: string;
  status: WorkflowStepStatus;
  notes?: string;
  summary?: string;
  assetPaths?: string[];
}

interface WorkflowTaskPatch {
  status?: string;
  priority?: "low" | "medium" | "high";
  board?: string;
  title?: string;
  tags?: string[];
  body?: string;
  binder?: string;
  group?: string;
}

export interface WorkflowFile {
  id: string;
  path: string;
  filename: string;
  extension: string;
  binder: string;
  content: string;
  readOnly: boolean;
  binderId?: string;
  baseHash?: string;
  version?: string;
}

export interface Mission {
  id: string;
  title: string;
  status: string;
  priority: string;
  description: string;
  taskIds: string[];
}

export interface MissionTaskBinderRow {
  workspace_id: string;
  mission: string;
  task: string;
  binder: string;
  title: string;
}

export interface WorkflowDefinition {
  id: string;
  name: string;
  description: string;
  schedule: string;
  steps: Array<{
    type: string;
    skill_id: string;
    params: Record<string, unknown>;
  }>;
  created_at: string;
  updated_at: string;
}

export interface WorkflowRun {
  run_id: string;
  workflow_id: string;
  workflow_name: string;
  started_at: string;
  finished_at: string;
  status: string;
  steps: Array<{
    index: number;
    type: string;
    skill_id: string;
    success: boolean;
    result?: Record<string, unknown>;
    error?: string;
  }>;
}

export interface WorkflowStatus {
  domain?: string;
  source_of_truth?: string;
  next_actions?: string[];
  tasker?: {
    boards: Array<{ name: string; count: number; path: string }>;
    total_tasks: number;
  };
  vault?: {
    ready: boolean;
    missing_layers: string[];
  };
  maintenance?: {
    scheduler_status: string;
    next_run: string;
  };
}

export const WORKFLOW_TABS: { id: WorkflowTab; label: string; icon: string }[] =
  [
    { id: "mission-control", label: "Workflow", icon: "schedule" },
    { id: "tasks", label: "Tasks", icon: "check" },
    { id: "queue", label: "Queue", icon: "pending_actions" },
    { id: "editor", label: "Editor", icon: "diamond" },
  ];

import { SNACKBAR_BASE } from "@/api/base";

const API = SNACKBAR_BASE;

function normalizeWorkflowTask(task: WorkflowTask): WorkflowTask {
  const steps = task.steps?.length
    ? task.steps.map((step, index) => ({
        id: step.id || `${task.id}:step-${index + 1}`,
        title: step.title || `Step ${index + 1}`,
        status: step.status || "todo",
        notes: step.notes || "",
        summary: step.summary || "",
        assetPaths: Array.isArray(step.assetPaths) ? step.assetPaths : [],
      }))
    : [];

  return {
    ...task,
    binder: task.binder || "",
    workspace: task.workspace || "User Vault",
    workflowType: task.workflowType || "user",
    summary: task.summary ?? task.description ?? "",
    notes: task.notes ?? "",
    assetPaths: Array.isArray(task.assetPaths) ? task.assetPaths : [],
    steps,
    completedAt: task.completedAt ?? null,
  };
}

function deriveTaskStatusFromSteps(steps: WorkflowStep[]): string {
  if (steps.length === 0) return "todo";
  if (steps.some((step) => step.status === "blocked")) return "blocked";
  if (steps.every((step) => step.status === "completed")) return "completed";
  if (steps.some((step) => step.status === "in-progress")) return "in-progress";
  return "todo";
}

function nextStepStatus(status: WorkflowStepStatus): WorkflowStepStatus {
  if (status === "todo") return "in-progress";
  if (status === "in-progress") return "completed";
  if (status === "completed") return "todo";
  return "todo";
}

const DEFAULT_EDITOR_FILE: WorkflowFile = {
  id: "system:welcome-ucode",
  path: "virtual/Welcome to uCode.md",
  filename: "Welcome to uCode.md",
  extension: "md",
  binder: "Sandbox",
  content: `# Welcome to uCode

Start writing in the Markdown editor right away.

## Quick start

- Use the left sidebar to open files from your vault.
- Switch edit mode between Prose and Code in the editor toolbar.
- Changes here are local until you save/publish through your workflow lane.
`,
  readOnly: false,
};

export const useWorkflowStore = defineStore("workflow", () => {
  const EDITOR_MODE_KEY = "ucore.workflow.editor-mode";
  const editorSurface = getEditorSurface();

  function readEditorMode(): "prose" | "code" {
    try {
      const saved = localStorage.getItem(EDITOR_MODE_KEY);
      return saved === "code" ? "code" : "prose";
    } catch {
      return "prose";
    }
  }

  const activeTab = ref<WorkflowTab>("mission-control");
  const activeList = ref("");
  const listNames = ref<string[]>([]);
  const activeBinderId = ref("");
  const binderStage = ref("brief");
  const binderCreateRequested = ref(false);
  const binders = ref<Array<{ id: string; title?: string; name?: string; state?: string }>>([]);
  const binderDocument = ref<WorkflowFile | null>(null);
  const editorDrafts = ref<Record<string, string>>({});
  const editorBaseHashes = ref<Record<string, string>>({});
  const tasks = ref<WorkflowTask[]>([]);
  const missions = ref<Mission[]>([]);
  const selectedTask = ref<WorkflowTask | null>(null);
  const selectedFile = ref<WorkflowFile | null>(null);
  const editorOpen = ref(false);
  // Note: side-by-side editor (showEditorPane, paneLayout) deprecated in favor of Markdown WYSIWYG
  const editorMode = ref<"prose" | "code">(readEditorMode());

  // Backend-fetched state
  const loading = ref(false);
  const error = ref<string | null>(null);
  const taskError = ref<string | null>(null);
  const workflowStatus = ref<WorkflowStatus | null>(null);
  const missionTaskBinderRows = ref<MissionTaskBinderRow[]>([]);
  const workflowDefinitions = ref<WorkflowDefinition[]>([]);
  const workflowRuns = ref<WorkflowRun[]>([]);
  const capabilityRepairs = ref<Record<string, CapabilityPreflightResult>>({});

  const taskLists = computed(() => [...new Set([...listNames.value, ...tasks.value.map(task => task.board), activeList.value])].filter(Boolean).sort());
  const scopedTasks = computed(() => tasks.value.filter(task =>
    (activeBinderId.value || !activeList.value || task.board === activeList.value) &&
    (!activeBinderId.value || task.binder === activeBinderId.value),
  ));
  const orderedContextTasks = computed(() => [...scopedTasks.value].sort((a, b) => {
    const ranks: Record<string, number> = { "in-progress": 0, todo: 1, blocked: 2, review: 3, completed: 4 };
    return (ranks[a.status] ?? 5) - (ranks[b.status] ?? 5) || a.title.localeCompare(b.title);
  }));
  const binderChoices = computed(() => [...new Set([...binders.value.map(binder => binder.id), ...tasks.value.map(task => task.binder || "")])].filter(Boolean).map(id => ({ id, title: binders.value.find(binder => binder.id === id)?.title || id, hasContent: binders.value.some(binder => binder.id === id) })));
  const relatedTasks = computed(() => selectedTask.value
    ? orderedContextTasks.value.filter(task => (task.group || "") === (selectedTask.value?.group || ""))
    : orderedContextTasks.value);
  const locationLabel = computed(() => (activeTab.value === "editor" && !selectedTask.value && !binderDocument.value && editorSurface.currentFile.value) ? editorSurface.currentFile.value.path : [
    activeBinderId.value ? (binders.value.find(binder => binder.id === activeBinderId.value)?.title || activeBinderId.value) : "",
    activeList.value,
    activeTab.value === "editor" ? selectedTask.value?.group : "",
  ].filter(Boolean).join(" / ") || "All tasks");
  const editorKey = computed(() => selectedTask.value ? `task:${selectedTask.value.id}` : editorSurface.currentFile.value?.path || selectedFile.value?.path || "");
  const hasEditorDraft = computed(() => Object.hasOwn(editorDrafts.value, editorKey.value));

  // Legacy list links may name a known Binder. Provider boards remain metadata.
  function setTaskContext(board = "", binder = "") {
    const resolvedBinder = binder || (binders.value.some(item => item.id === board) ? board : "");
    activeBinderId.value = resolvedBinder;
    activeList.value = resolvedBinder ? "" : board;
  }
  function showList(board = "", binder = "") {
    setTaskContext(board, binder);
    activeTab.value = "tasks";
  }
  function showBinder(id: string) {
    activeBinderId.value = id;
    activeList.value = "";
    activeTab.value = "mission-control";
  }
  function openTask(task: WorkflowTask) {
    selectTask(task);
    setTaskContext(task.board, task.binder || "");
    activeTab.value = "editor";
  }
  async function fetchLists() {
    const response = await fetch(`${API}/api/workflow/lists`, { signal: AbortSignal.timeout(8000) });
    if (!response.ok) throw new Error("Could not load task lists");
    const data = await response.json();
    listNames.value = (data.boards || []).map((board: { name: string }) => board.name);
  }
  async function createList(name: string) {
    const response = await fetch(`${API}/api/workflow/lists`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name }), signal: AbortSignal.timeout(8000) });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Could not create list");
    await fetchLists();
    showList(data.name);
  }
  let binderFetch: Promise<void> | null = null;
  async function fetchBinders(force = false): Promise<void> {
    if (binderFetch) { await binderFetch; if (!force) return; }
    const work = (async () => {
      const response = await fetch(`${API}/api/binder/list`, { signal: AbortSignal.timeout(8000) });
      if (!response.ok) throw new Error("Could not load binders");
      const data = await response.json();
      binders.value = (data.binders || []).map((binder: any) => ({ ...binder, id: binder.id || binder.name }));
    })();
    binderFetch = work;
    try { await work; } finally { if (binderFetch === work) binderFetch = null; }
  }
  function openBinderDocument(id: string, title: string, content: string, baseHash = "", readOnly = false) {
    activeBinderId.value = id;
    activeList.value = "";
    const file: WorkflowFile = { id: `binder:${id}`, path: `binder:${id}/${readOnly ? "brief" : "draft"}`, filename: title, content, readOnly, binder: id, binderId: id, baseHash, extension: "md" };
    if (!Object.hasOwn(editorDrafts.value, file.path)) editorBaseHashes.value[file.path] = baseHash;
    file.baseHash = editorBaseHashes.value[file.path] ?? baseHash;
    selectFile(file);
    binderDocument.value = file;
  }
  async function saveBinderDocument(content: string) {
    const file = binderDocument.value;
    if (!file || file.readOnly) throw new Error("Open an editable binder draft first");
    const response = await fetch(`${API}/api/binder/${encodeURIComponent(file.binderId!)}/draft`, {
      method: "PATCH", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content, expected_base_hash: file.baseHash }), signal: AbortSignal.timeout(15000),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.message || data.error || "Could not save binder draft");
    file.baseHash = data.draft_sha256;
    editorBaseHashes.value[file.path] = data.draft_sha256;
    file.content = content;
    editorSurface.updateContent(content);
    delete editorDrafts.value[editorKey.value];
  }
  async function createTask(title: string, board = activeList.value || "inbox", binder = activeBinderId.value, group = "") {
    const response = await fetch(`${API}/api/workflow/tasks`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ title, board, binder, group }), signal: AbortSignal.timeout(8000) });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Could not create task");
    await fetchTasks(true);
    const task = tasks.value.find(task => task.id === data.updated.id);
    if (task) openTask(task);
    return data.updated;
  }
  async function duplicateTask(taskId: string, destination: { board?: string; binder?: string; group?: string } = {}) {
    const response = await fetch(`${API}/api/workflow/tasks/${encodeURIComponent(taskId)}/duplicate`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(destination), signal: AbortSignal.timeout(8000) });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Could not copy task");
    await fetchTasks(true);
    return data.updated;
  }
  function startTaskDrag(event: DragEvent, task: WorkflowTask) {
    event.dataTransfer?.setData("application/x-ucore-task", task.id);
    event.dataTransfer?.setData("text/plain", task.id);
    if (event.dataTransfer) event.dataTransfer.effectAllowed = "copyMove";
  }
  async function dropTask(event: DragEvent, destination: { board?: string; binder?: string; group?: string; status?: string }) {
    const taskId = event.dataTransfer?.getData("application/x-ucore-task");
    if (!taskId) return;
    if (event.altKey || event.ctrlKey) await duplicateTask(taskId, destination);
    else await patchTask(taskId, destination);
  }

  async function preflightOrBlock(capability: string): Promise<boolean> {
    try {
      const result = await ensureCapabilityReady(capability);
      capabilityRepairs.value[capability] = result;
      return true;
    } catch (e: any) {
      const preflight = e?.preflight as CapabilityPreflightResult | undefined;
      if (preflight) {
        capabilityRepairs.value[capability] = preflight;
        error.value = `Capability '${capability}' is not ready. Complete repair steps before retrying.`;
      } else {
        error.value =
          e?.message || `Capability preflight failed: ${capability}`;
      }
      return false;
    }
  }

  const recheckingCapabilities = ref(false);

  async function retryCapabilityPreflight(): Promise<void> {
    if (recheckingCapabilities.value) return;
    recheckingCapabilities.value = true;
    try {
      const blocked = Object.values(capabilityRepairs.value)
        .filter((item) => !item.ready)
        .map((item) => item.capability);
      await fetchAll();
      await Promise.all(blocked.map((capability) => preflightOrBlock(capability)));
      if (Object.values(capabilityRepairs.value).every((item) => item.ready)) {
        error.value = null;
      }
    } finally {
      recheckingCapabilities.value = false;
    }
  }

  function setTab(tab: WorkflowTab) {
    if (tab === "binder" || tab === "research") tab = "mission-control";
    if (tab === "editor" && selectedTask.value) {
      setTaskContext(selectedTask.value.board, selectedTask.value.binder || "");
    } else if (tab === "editor" && binderDocument.value) {
      activeList.value = "";
      activeBinderId.value = binderDocument.value.binderId || "";
    }
    activeTab.value = tab;
  }

  const activeTasks = computed(() => {
    return tasks.value.filter((task) => !["completed", "superseded", "cancelled", "archived"].includes(task.status));
  });

  const flowLogTasks = computed(() => {
    return [...tasks.value.filter((task) => task.status === "completed")].sort(
      (a, b) =>
        String(b.completedAt || "").localeCompare(String(a.completedAt || "")),
    );
  });

  const tasksByStatus = computed(() => {
    const groups: Record<string, WorkflowTask[]> = {
      todo: [],
      "in-progress": [],
      review: [],
      blocked: [],
      completed: [],
    };
    for (const t of activeTasks.value) {
      if (!groups[t.status]) groups[t.status] = [];
      groups[t.status].push(t);
    }
    return groups;
  });

  const totalTasks = computed(() => tasks.value.length);
  const inProgressCount = computed(
    () => activeTasks.value.filter((t) => t.status === "in-progress").length,
  );
  const completedCount = computed(() => flowLogTasks.value.length);

  /** Fetch overall workflow status from user endpoint with legacy fallback */
  async function fetchWorkflowStatus(): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      let res = await fetch(`${API}/api/user/workflow/status`, {
        signal: AbortSignal.timeout(8000),
      });
      if (res.status === 404) {
        res = await fetch(`${API}/api/system/workflow`, {
          signal: AbortSignal.timeout(8000),
        });
      }
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      workflowStatus.value = data;
      // Populate tasks from tasker boards if available
      if (data.tasker?.boards) {
        // Merge counts into missions for now
      }
    } catch (e: any) {
      error.value = e.message || "Failed to fetch workflow status";
      console.warn("Workflow status fetch failed, keeping last loaded data", e);
    } finally {
      loading.value = false;
    }
  }

  /** Fetch tasks from backend /api/workflow/tasks */
  let tasksFetch: Promise<void> | null = null;
  async function fetchTasks(force = false): Promise<void> {
    if (tasksFetch) { await tasksFetch; if (!force) return; }
    const work = fetchTasksSnapshot();
    tasksFetch = work;
    try { await work; } finally { if (tasksFetch === work) tasksFetch = null; }
  }
  async function fetchTasksSnapshot(): Promise<void> {
    taskError.value = null;
    if (!(await preflightOrBlock("workflow.run"))) return;
    loading.value = true;
    error.value = null;
    try {
      const res = await fetch(`${API}/api/workflow/tasks?scope=user`, {
        signal: AbortSignal.timeout(8000),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (Array.isArray(data.tasks)) {
        const mapped = data.tasks.map((t: any) =>
          normalizeWorkflowTask({
            id: t.id || t.source_id || "",
            title: t.title || "Untitled",
            status: t.status || "todo",
            priority: t.priority || "medium",
            board: t.board || "general",
            tags: Array.isArray(t.tags)
              ? t.tags.map((tag: unknown) => String(tag))
              : [],
            description: t.description || t.summary || "",
            binder: t.binder,
            group: t.group || "",
            workspace: t.workspace,
            workflowType: t.workflow_type || t.workflowType,
            summary: t.summary,
            notes: t.notes,
            assetPaths: Array.isArray(t.asset_paths)
              ? t.asset_paths.map((path: unknown) => String(path))
              : Array.isArray(t.assetPaths)
                ? t.assetPaths.map((path: unknown) => String(path))
                : [],
            steps: Array.isArray(t.steps)
              ? t.steps.map((step: any, index: number) => ({
                  id:
                    step.id ||
                    `${t.id || t.source_id || "task"}:step-${index + 1}`,
                  title: step.title || `Step ${index + 1}`,
                  status: step.status || "todo",
                  notes: step.notes || "",
                  summary: step.summary || "",
                  assetPaths: Array.isArray(step.assetPaths)
                    ? step.assetPaths.map((path: unknown) => String(path))
                    : [],
                }))
              : undefined,
            completedAt: t.completed_at || t.completedAt || null,
          }),
        );
        tasks.value = mapped;
      }
    } catch (e: any) {
      taskError.value = e.message || "Failed to fetch tasks";
      error.value = taskError.value;
      console.warn("Tasks fetch failed, keeping last loaded data", e);
    } finally {
      loading.value = false;
    }
  }

  async function patchTask(
    taskId: string,
    patch: WorkflowTaskPatch,
  ): Promise<WorkflowTask> {
    if (!(await preflightOrBlock("workflow.run"))) {
      throw new Error("workflow.run capability not ready");
    }

    const res = await fetch(
      `${API}/api/workflow/tasks/${encodeURIComponent(taskId)}`,
      {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(patch),
        signal: AbortSignal.timeout(8000),
      },
    );
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }

    const data = await res.json();
    const updated = data?.updated || {};
    const existing = tasks.value.find((task) => task.id === taskId);
    const mapped: WorkflowTask = normalizeWorkflowTask({
      id: String(updated.id || taskId),
      title: String(updated.title || "Untitled"),
      status: String(updated.status || "todo"),
      priority: String(updated.priority || "medium") as
        | "low"
        | "medium"
        | "high",
      board: String(updated.board || "general"),
      tags: Array.isArray(updated.tags)
        ? updated.tags.map((tag: unknown) => String(tag))
        : [],
      description: String(updated.description || updated.body || ""),
      binder: String(updated.binder ?? patch.binder ?? existing?.binder ?? ""),
      group: String(updated.group ?? patch.group ?? existing?.group ?? ""),
      workspace: String(
        updated.workspace || existing?.workspace || "User Vault",
      ),
      workflowType: (updated.workflowType ||
        existing?.workflowType ||
        "user") as "user" | "developer" | "system" | "autonomous",
      summary: String(updated.summary || existing?.summary || ""),
      notes: String(updated.notes || existing?.notes || ""),
      assetPaths: Array.isArray(updated.assetPaths)
        ? updated.assetPaths.map((path: unknown) => String(path))
        : existing?.assetPaths || [],
      steps: Array.isArray(updated.steps)
        ? updated.steps.map((step: any, index: number) => ({
            id: step.id || `${taskId}:step-${index + 1}`,
            title: step.title || `Step ${index + 1}`,
            status: step.status || "todo",
            notes: step.notes || "",
            summary: step.summary || "",
            assetPaths: Array.isArray(step.assetPaths)
              ? step.assetPaths.map((path: unknown) => String(path))
              : [],
          }))
        : existing?.steps,
      completedAt:
        updated.completedAt ||
        updated.completed_at ||
        (String(updated.status || existing?.status || "todo") === "completed"
          ? existing?.completedAt || new Date().toISOString()
          : null),
    });

    const idx = tasks.value.findIndex((task) => task.id === taskId);
    if (idx >= 0) tasks.value[idx] = mapped;
    else tasks.value.push(mapped);
    if (selectedTask.value?.id === taskId) {
      selectedTask.value = mapped;
      if (activeTab.value === "editor") {
        setTaskContext(mapped.board, mapped.binder || "");
      }
    }
    if ("body" in patch) delete editorDrafts.value[`task:${taskId}`];
    return mapped;
  }

  /** Fetch mission/task/binder projections from /api/knowledge/adapter/mission-task-binder */
  async function fetchMissionTaskBinder(workspaceId?: string): Promise<void> {
    if (!(await preflightOrBlock("knowledge.search"))) return;
    loading.value = true;
    error.value = null;
    try {
      const params = new URLSearchParams({ limit: "100" });
      if (workspaceId) params.set("workspace_id", workspaceId);
      const res = await fetch(
        `${API}/api/knowledge/adapter/mission-task-binder?${params.toString()}`,
        {
          signal: AbortSignal.timeout(8000),
        },
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (Array.isArray(data.rows)) {
        missionTaskBinderRows.value = data.rows;
        // Build missions from unique mission values
        const missionMap = new Map<string, MissionTaskBinderRow[]>();
        for (const row of data.rows) {
          const key = row.mission || "Unknown Mission";
          if (!missionMap.has(key)) missionMap.set(key, []);
          missionMap.get(key)!.push(row);
        }
        missions.value = Array.from(missionMap.entries()).map(
          ([title, rows], idx) => ({
            id: `mtb-${idx}`,
            title,
            status: "active",
            priority: "medium",
            description: `${rows.length} tasks across ${new Set(rows.map((r) => r.binder)).size} binders`,
            taskIds: rows.map((r) => r.task),
          }),
        );
      }
    } catch (e: any) {
      error.value = e.message || "Failed to fetch mission/task binder data";
      console.warn("Mission/task binder fetch failed, keeping last loaded data", e);
    } finally {
      loading.value = false;
    }
  }

  /** Fetch workflow definitions from /api/workflows */
  async function fetchWorkflowDefinitions(): Promise<void> {
    if (!(await preflightOrBlock("workflow.run"))) return;
    loading.value = true;
    error.value = null;
    try {
      const res = await fetch(`${API}/api/workflows`, {
        signal: AbortSignal.timeout(8000),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (Array.isArray(data.workflows)) {
        workflowDefinitions.value = data.workflows;
      }
    } catch (e: any) {
      error.value = e.message || "Failed to fetch workflow definitions";
      console.warn("Workflow definitions fetch failed", e);
    } finally {
      loading.value = false;
    }
  }

  /** Fetch recent workflow runs from /api/workflows/runs */
  async function fetchWorkflowRuns(): Promise<void> {
    if (!(await preflightOrBlock("workflow.run"))) return;
    loading.value = true;
    error.value = null;
    try {
      const res = await fetch(`${API}/api/workflows/runs?limit=20`, {
        signal: AbortSignal.timeout(8000),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (Array.isArray(data.runs)) {
        workflowRuns.value = data.runs;
      }
    } catch (e: any) {
      error.value = e.message || "Failed to fetch workflow runs";
      console.warn("Workflow runs fetch failed", e);
    } finally {
      loading.value = false;
    }
  }

  /** Fetch all data for the current surface at once */
  async function fetchAll(): Promise<void> {
    await Promise.allSettled([
      fetchBinders(),
      fetchWorkflowStatus(),
      fetchTasks(),
      fetchWorkflowDefinitions(),
      fetchWorkflowRuns(),
    ]);
    // Read-only dashboard hydration is resilient across older uCore backends.
    // When cached/seeded tasks are available, optional 404s must not replace a
    // usable workflow with a blocking error banner. Mutations still perform
    // strict capability preflight in patch/archive/reset actions.
    if (tasks.value.length > 0 || missions.value.length > 0) {
      error.value = null;
    }
  }

  async function archiveUserWorkflow(reason = "manual"): Promise<unknown> {
    const res = await fetch(`${API}/api/user/workflow/archive`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reason }),
      signal: AbortSignal.timeout(30000),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  }

  async function resetUserWorkflow(reason = "reset"): Promise<unknown> {
    const res = await fetch(`${API}/api/user/workflow/reset`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reason }),
      signal: AbortSignal.timeout(60000),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    await fetchAll();
    return data;
  }

  async function seedUserWorkflow(reason = "seed-only"): Promise<unknown> {
    const res = await fetch(`${API}/api/user/workflow/seed`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reason }),
      signal: AbortSignal.timeout(30000),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    await fetchAll();
    return data;
  }

  /**
   * Select a task for viewing/editing.
   *
   * When `openSideEditor` is true (default), the side-column editor opens
   * alongside the current tab.  Set it to `false` when the caller manages
   * its own inline editor (e.g. TasksPanel code-only view).
   */
  function selectTask(task: WorkflowTask, openSideEditor = true) {
    editorSurface.closeEditor();
    binderDocument.value = null;
    selectedFile.value = null;
    selectedTask.value = task;
    editorOpen.value = openSideEditor;
    // Stay on the current tab — TasksPanel controls its own inline editor
  }

  async function openVaultDocument(path: string, filename: string, binder: string) {
    const workspace = useWorkspaceStore();
    workspace.error = "";
    await workspace.selectFile({ id: path, path, name: filename, type: "file", extension: "md" });
    const file = editorSurface.currentFile.value;
    if (!file || file.path !== path || (workspace.error && workspace.error !== "Offline copy")) {
      throw new Error(workspace.error || "Could not open document");
    }
    selectFile({ ...file, id: path, binder, readOnly: Boolean(file.readOnly) });
  }

  function selectFile(file: WorkflowFile) {
    if (!file.binderId) {
      activeBinderId.value = binders.value.find(binder => binder.id === file.binder)?.id || "";
      activeList.value = "";
    }
    binderDocument.value = null;
    selectedTask.value = null;
    selectedFile.value = {
      ...file,
      binder: file.binder || "Sandbox",
    };
    editorSurface.openFile({
      path: selectedFile.value.path,
      filename: selectedFile.value.filename,
      content: selectedFile.value.content,
      extension: selectedFile.value.extension,
      readOnly: selectedFile.value.readOnly,
      version: selectedFile.value.version,
    });
    editorOpen.value = true;
    activeTab.value = "editor";
  }

  function updateTaskNotes(taskId: string, notes: string) {
    const task = tasks.value.find((item) => item.id === taskId);
    if (!task) return;
    task.notes = notes;
  }

  function updateTaskSummary(taskId: string, summary: string) {
    const task = tasks.value.find((item) => item.id === taskId);
    if (!task) return;
    task.summary = summary;
  }

  function updateTaskStep(
    taskId: string,
    stepId: string,
    patch: Partial<WorkflowStep>,
  ) {
    const task = tasks.value.find((item) => item.id === taskId);
    if (!task || !task.steps) return;
    const step = task.steps.find((item) => item.id === stepId);
    if (!step) return;
    Object.assign(step, patch);
  }

  function cycleTaskStep(taskId: string, stepId: string) {
    const task = tasks.value.find((item) => item.id === taskId);
    if (!task || !task.steps) return;
    const step = task.steps.find((item) => item.id === stepId);
    if (!step) return;
    step.status = nextStepStatus(step.status);
    const nextStatus = deriveTaskStatusFromSteps(task.steps);
    task.status = nextStatus;
    task.completedAt =
      nextStatus === "completed"
        ? task.completedAt || new Date().toISOString()
        : null;
  }

  function updateTaskStatus(taskId: string, status: string) {
    const task = tasks.value.find((item) => item.id === taskId);
    if (!task) return;
    task.status = status;
    task.completedAt =
      status === "completed"
        ? task.completedAt || new Date().toISOString()
        : null;
  }

  function updateTaskAssetPaths(taskId: string, assetPaths: string[]) {
    const task = tasks.value.find((item) => item.id === taskId);
    if (!task) return;
    task.assetPaths = assetPaths;
  }

  function ensureDefaultEditorFile() {
    if (selectedTask.value || selectedFile.value) {
      return;
    }
    selectedFile.value = { ...DEFAULT_EDITOR_FILE };
    editorSurface.openFile({
      path: selectedFile.value.path,
      filename: selectedFile.value.filename,
      content: selectedFile.value.content,
      extension: selectedFile.value.extension,
      readOnly: selectedFile.value.readOnly,
    });
    editorOpen.value = true;
  }

  function closeEditor() {
    editorOpen.value = false;
    selectedTask.value = null;
    selectedFile.value = null;
    editorSurface.closeEditor();
  }

  function updateEditorContent(value: string) {
    if (editorKey.value) editorDrafts.value[editorKey.value] = value;
    if (!selectedTask.value) editorSurface.updateContent(value);
  }

  // toggleEditorPane and togglePaneLayout deprecated with side-by-side editor

  function setEditorMode(mode: "prose" | "code") {
    editorMode.value = mode;
    try {
      localStorage.setItem(EDITOR_MODE_KEY, mode);
    } catch {
      // no-op: persistence is best-effort in restricted environments
    }
  }

  return {
    activeList, activeBinderId, binderStage, binderCreateRequested, binders, binderDocument, editorDrafts,
    taskLists, binderChoices, scopedTasks, orderedContextTasks, relatedTasks, locationLabel, editorKey, hasEditorDraft,
    setTaskContext, showList, showBinder, openTask, openBinderDocument, saveBinderDocument, fetchBinders,
    createTask, duplicateTask, startTaskDrag, dropTask, fetchLists, createList,
    activeTab,
    tasks,
    activeTasks,
    flowLogTasks,
    missions,
    selectedTask,
    selectedFile,
    editorOpen,

    editorMode,
    loading,
    error,
    taskError,
    workflowStatus,
    missionTaskBinderRows,
    workflowDefinitions,
    workflowRuns,
    capabilityRepairs,
    totalTasks,
    inProgressCount,
    completedCount,
    tasksByStatus,
    setTab,
    selectTask,
    selectFile, openVaultDocument,
    updateTaskNotes,
    updateTaskSummary,
    updateTaskStep,
    cycleTaskStep,
    updateTaskStatus,
    updateTaskAssetPaths,
    ensureDefaultEditorFile,
    closeEditor,
    updateEditorContent,

    setEditorMode,
    fetchWorkflowStatus,
    fetchTasks,
    fetchMissionTaskBinder,
    fetchWorkflowDefinitions,
    fetchWorkflowRuns,
    fetchAll,
    retryCapabilityPreflight,
    recheckingCapabilities,
    patchTask,
    archiveUserWorkflow,
    resetUserWorkflow,
    seedUserWorkflow,
  };
});

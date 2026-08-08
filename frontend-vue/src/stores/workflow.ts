/**
 * @module stores/workflow
 * @description Workflow surface state — tasks, missions, binder, publish, kanban.
 * Wires to backend /api/workflows/*, /api/system/workflow, /api/workflow/tasks,
 * and /api/knowledge/adapter/mission-task-binder endpoints.
 */
import { defineStore } from "pinia";
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
  | "editor"
  | "publish";

export interface WorkflowTask {
  id: string;
  title: string;
  status: string;
  priority: "low" | "medium" | "high";
  board: string;
  tags: string[];
  description: string;
  binder?: string;
  workspace?: string;
  workflowType?: "user" | "developer" | "system" | "autonomous";
  summary?: string;
  notes?: string;
  assetPaths?: string[];
  steps?: WorkflowStep[];
  completedAt?: string | null;
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
}

export interface WorkflowFile {
  id: string;
  path: string;
  filename: string;
  extension: string;
  binder: string;
  content: string;
  readOnly: boolean;
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
  appflowy?: {
    status: string;
    mode: string;
    enabled_by_default: boolean;
    available: boolean;
    database_count: number;
    workspace_count: number;
    errors: string[];
  };
  maintenance?: {
    scheduler_status: string;
    next_run: string;
  };
}

export const WORKFLOW_TABS: { id: WorkflowTab; label: string; icon: string }[] =
  [
    { id: "mission-control", label: "Mission Control", icon: "dashboard" },
    { id: "binder", label: "Binder", icon: "folder" },
    { id: "tasks", label: "Tasks", icon: "task" },
    { id: "editor", label: "Editor", icon: "article" },
    { id: "publish", label: "Publish", icon: "publish" },
  ];

import { SNACKBAR_BASE } from "@/api/base";

const API = SNACKBAR_BASE;

const SAMPLE_TASKS: WorkflowTask[] = [
  {
    id: "seed-1",
    title: "Plan the week",
    status: "in-progress",
    priority: "high",
    board: "planning",
    tags: ["planning", "weekly"],
    description: "Review goals and lock top priorities for the week.",
  },
  {
    id: "seed-2",
    title: "Draft article outline",
    status: "todo",
    priority: "medium",
    board: "writing",
    tags: ["writing", "content"],
    description: "Create a clear outline before drafting full sections.",
  },
  {
    id: "seed-3",
    title: "Organize life admin docs",
    status: "review",
    priority: "medium",
    board: "admin",
    tags: ["admin", "records"],
    description: "Collect invoices, reminders, and account documents.",
  },
  {
    id: "seed-4",
    title: "Summarize this week learning",
    status: "completed",
    priority: "low",
    board: "learning",
    tags: ["learning", "weekly-review"],
    description: "Publish a short recap with key ideas and next actions.",
  },
  {
    id: "seed-5",
    title: "Schedule health appointments",
    status: "todo",
    priority: "high",
    board: "personal",
    tags: ["health", "personal"],
    description: "Book pending checkups and note preparation items.",
  },
  {
    id: "seed-6",
    title: "Prepare monthly budget review",
    status: "blocked",
    priority: "medium",
    board: "finance",
    tags: ["finance", "planning"],
    description: "Waiting for final bank export before reconciliation.",
  },
];

const SAMPLE_MISSIONS: Mission[] = [
  {
    id: "m1",
    title: "Weekly Planning",
    status: "active",
    priority: "high",
    description: "Lock in top priorities and review goals for the week",
    taskIds: ["seed-1"],
  },
  {
    id: "m2",
    title: "Content Pipeline",
    status: "active",
    priority: "medium",
    description: "Outline, draft, and publish articles for the month",
    taskIds: ["seed-2"],
  },
  {
    id: "m3",
    title: "Health & Admin",
    status: "active",
    priority: "medium",
    description: "Book appointments, organize admin documents, budget review",
    taskIds: ["seed-4", "seed-5", "seed-6"],
  },
];

function createDefaultSteps(
  taskId: string,
  title: string,
  status: string,
): WorkflowStep[] {
  const labels = ["Plan", "Draft", "Review", "Publish"];
  return labels.map((label, index) => ({
    id: `${taskId}:step-${index + 1}`,
    title: `${label} ${title}`,
    status:
      status === "completed"
        ? "completed"
        : status === "blocked" && index === 0
          ? "blocked"
          : index === 0 && status === "in-progress"
            ? "in-progress"
            : "todo",
    notes: "",
    summary: "",
    assetPaths: [],
  }));
}

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
    : createDefaultSteps(task.id, task.title, task.status);

  return {
    ...task,
    binder: task.binder || "Sandbox",
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

Start writing in Bangle right away.

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
  const tasks = ref<WorkflowTask[]>(SAMPLE_TASKS.map(normalizeWorkflowTask));
  const missions = ref<Mission[]>(SAMPLE_MISSIONS);
  const selectedTask = ref<WorkflowTask | null>(null);
  const selectedFile = ref<WorkflowFile | null>(null);
  const editorOpen = ref(false);
  const showEditorPane = ref(false);
  const paneLayout = ref<"split" | "stacked">("stacked");
  const editorMode = ref<"prose" | "code">(readEditorMode());

  // Backend-fetched state
  const loading = ref(false);
  const error = ref<string | null>(null);
  const workflowStatus = ref<WorkflowStatus | null>(null);
  const missionTaskBinderRows = ref<MissionTaskBinderRow[]>([]);
  const workflowDefinitions = ref<WorkflowDefinition[]>([]);
  const workflowRuns = ref<WorkflowRun[]>([]);
  const capabilityRepairs = ref<Record<string, CapabilityPreflightResult>>({});

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

  function setTab(tab: WorkflowTab) {
    activeTab.value = tab;
  }

  const activeTasks = computed(() => {
    return tasks.value.filter((task) => task.status !== "completed");
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
      console.warn("Workflow status fetch failed, using sample data", e);
    } finally {
      loading.value = false;
    }
  }

  /** Fetch tasks from backend /api/workflow/tasks */
  async function fetchTasks(): Promise<void> {
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
        tasks.value =
          mapped.length > 0
            ? mapped
            : [...SAMPLE_TASKS.map(normalizeWorkflowTask)];
      }
    } catch (e: any) {
      error.value = e.message || "Failed to fetch tasks";
      console.warn("Tasks fetch failed, using sample data", e);
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
      binder: String(updated.binder || existing?.binder || "Sandbox"),
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
    if (idx >= 0) {
      tasks.value[idx] = mapped;
    }
    if (selectedTask.value?.id === taskId) {
      selectedTask.value = mapped;
    }
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
      console.warn("Mission/task binder fetch failed, using sample data", e);
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
      fetchWorkflowStatus(),
      fetchTasks(),
      fetchMissionTaskBinder(),
      fetchWorkflowDefinitions(),
      fetchWorkflowRuns(),
    ]);
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

  function selectTask(task: WorkflowTask) {
    selectedFile.value = null;
    selectedTask.value = task;
    editorOpen.value = true;
    // Stay on the tasks tab — editor opens alongside it as a column
  }

  function selectFile(file: WorkflowFile) {
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
    });
    editorOpen.value = true;
    showEditorPane.value = true;
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
    showEditorPane.value = true;
  }

  function closeEditor() {
    editorOpen.value = false;
    selectedTask.value = null;
    selectedFile.value = null;
    showEditorPane.value = true;
    editorSurface.closeEditor();
  }

  function updateEditorContent(value: string) {
    if (selectedTask.value) {
      selectedTask.value.description = value;
    }
    if (selectedFile.value) {
      selectedFile.value.content = value;
    }
    editorSurface.updateContent(value);
  }

  function toggleEditorPane() {
    showEditorPane.value = !showEditorPane.value;
  }

  function togglePaneLayout() {
    paneLayout.value = paneLayout.value === "split" ? "stacked" : "split";
  }

  function setEditorMode(mode: "prose" | "code") {
    editorMode.value = mode;
    try {
      localStorage.setItem(EDITOR_MODE_KEY, mode);
    } catch {
      // no-op: persistence is best-effort in restricted environments
    }
  }

  return {
    activeTab,
    tasks,
    activeTasks,
    flowLogTasks,
    missions,
    selectedTask,
    selectedFile,
    editorOpen,
    showEditorPane,
    paneLayout,
    editorMode,
    loading,
    error,
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
    selectFile,
    updateTaskNotes,
    updateTaskSummary,
    updateTaskStep,
    cycleTaskStep,
    updateTaskStatus,
    updateTaskAssetPaths,
    ensureDefaultEditorFile,
    closeEditor,
    updateEditorContent,
    toggleEditorPane,
    togglePaneLayout,
    setEditorMode,
    fetchWorkflowStatus,
    fetchTasks,
    fetchMissionTaskBinder,
    fetchWorkflowDefinitions,
    fetchWorkflowRuns,
    fetchAll,
    patchTask,
    archiveUserWorkflow,
    resetUserWorkflow,
    seedUserWorkflow,
  };
});

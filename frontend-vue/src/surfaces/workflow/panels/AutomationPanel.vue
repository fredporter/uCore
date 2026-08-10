<template>
  <div class="wf-panel">
    <div class="wf-panel__main">
      <!-- Compact toolbar -->
      <div class="wf-toolbar">
        <span class="wf-toolbar__count">
          <UIcon name="science" />
          Knowledge Automation
        </span>
        <UBadge :type="engineAvailable ? 'success' : 'error'" size="sm">
          {{ engineAvailable ? "engine ready" : "engine missing" }}
        </UBadge>
      </div>

      <p v-if="!engineAvailable" class="wf-automation-missing">
        Automation engine not found at
        <code>~/Code/uDev/automation/engine.py</code>.
      </p>

      <!-- Pipeline controls -->
      <div class="wf-automation-actions">
        <UButton
          variant="primary"
          size="sm"
          icon="play_arrow"
          :disabled="!engineAvailable || running"
          @click="runPipeline(false)"
        >
          {{ running ? "Running..." : "Run Pipeline" }}
        </UButton>
        <UButton
          variant="secondary"
          size="sm"
          icon="visibility"
          :disabled="!engineAvailable || running"
          @click="runPipeline(true)"
        >
          Dry Run
        </UButton>
        <UButton
          variant="secondary"
          size="sm"
          icon="add"
          @click="createNotebook"
        >
          New Notebook
        </UButton>
      </div>

      <!-- Run output -->
      <div
        v-if="output"
        class="wf-automation-output"
        :class="{ 'wf-automation-output--error': !outputOk }"
      >
        <pre>{{ output }}</pre>
      </div>

      <!-- ── Notebook Cell Editor ──────────────────────────────────── -->
      <div v-if="activeNotebook" class="nb-editor">
        <div class="nb-editor__toolbar">
          <button class="wf-editor-back-btn" @click="closeNotebook">
            <UIcon name="arrow_back" />
          </button>
          <span class="nb-editor__title">{{ activeNotebook.name }}</span>
          <UButton
            size="sm"
            variant="secondary"
            icon="play_arrow"
            :disabled="runningAll"
            @click="runAllCells"
          >
            {{ runningAll ? "Running..." : "Run All" }}
          </UButton>
          <UButton
            size="sm"
            variant="secondary"
            icon="save"
            @click="saveNotebook"
          >
            Save
          </UButton>
        </div>

        <div class="nb-editor__cells">
          <div
            v-for="(cell, idx) in cells"
            :key="cell.id"
            class="nb-cell"
            :class="`nb-cell--${cell.type}`"
          >
            <div class="nb-cell__gutter">
              <span class="nb-cell__index">[{{ idx + 1 }}]</span>
              <button
                v-if="cell.type === 'code'"
                class="nb-cell__run-btn"
                title="Run cell"
                :disabled="cell.running"
                @click="runCell(idx)"
              >
                <UIcon :name="cell.running ? 'sync' : 'play_arrow'" />
              </button>
            </div>
            <div class="nb-cell__body">
              <textarea
                v-if="cell.type === 'code'"
                v-model="cell.source"
                class="nb-cell__input"
                rows="3"
                placeholder="# Python code..."
                @keydown.ctrl.enter="runCell(idx)"
                @keydown.meta.enter="runCell(idx)"
              />
              <textarea
                v-else
                v-model="cell.source"
                class="nb-cell__input nb-cell__input--md"
                rows="2"
                placeholder="Markdown text..."
              />
              <div
                v-if="cell.output"
                class="nb-cell__output"
                :class="{ 'nb-cell__output--error': cell.error }"
              >
                <pre>{{ cell.output }}</pre>
              </div>
            </div>
            <div class="nb-cell__actions">
              <button
                class="nb-cell__type-btn"
                :title="
                  cell.type === 'code' ? 'Switch to Markdown' : 'Switch to Code'
                "
                @click="toggleCellType(idx)"
              >
                <UIcon :name="cell.type === 'code' ? 'article' : 'code'" />
              </button>
              <button
                class="nb-cell__del-btn"
                title="Delete cell"
                @click="deleteCell(idx)"
              >
                <UIcon name="close" />
              </button>
            </div>
          </div>
        </div>

        <!-- Add cell buttons -->
        <div class="nb-editor__add-bar">
          <button class="nb-add-btn" @click="addCell('code')">
            <UIcon name="add" /> Code
          </button>
          <button class="nb-add-btn" @click="addCell('markdown')">
            <UIcon name="add" /> Markdown
          </button>
        </div>
      </div>

      <!-- ── Notebooks list (when no notebook is active) ──────────── -->
      <div v-else class="wf-automation-notebooks">
        <div class="wf-toolbar">
          <span class="wf-toolbar__count"
            >{{ notebooks.length }} notebooks</span
          >
          <UButton
            variant="secondary"
            size="sm"
            icon="refresh"
            :disabled="loading"
            @click="loadStatus"
          >
            Refresh
          </UButton>
        </div>

        <div v-if="notebooks.length === 0" class="wf-automation-empty">
          No notebooks yet. Run the pipeline or create one above.
        </div>

        <div v-else class="wf-automation-notebook-list">
          <div
            v-for="nb in notebooks"
            :key="nb.path"
            class="wf-automation-notebook-row"
            @click="openNotebookEditor(nb)"
          >
            <UIcon name="description" />
            <div class="wf-automation-notebook-info">
              <span class="wf-automation-notebook-name">{{ nb.name }}</span>
              <span class="wf-automation-notebook-path">{{ nb.path }}</span>
            </div>
            <span class="wf-automation-notebook-meta">
              {{ formatSize(nb.size) }} · {{ formatDate(nb.mtime) }}
            </span>
            <UButton
              variant="secondary"
              size="sm"
              icon="open_in_new"
              @click.stop="openNotebook(nb)"
            >
              Raw
            </UButton>
          </div>
        </div>
      </div>

      <!-- Recent workflow runs -->
      <div v-if="wf.workflowRuns.length > 0" class="wf-section">
        <h4 class="wf-section-title">Recent Runs</h4>
        <div class="wf-run-log">
          <div
            v-for="run in wf.workflowRuns.slice(0, 10)"
            :key="run.run_id"
            class="wf-run-row"
          >
            <UBadge
              :type="
                run.status === 'completed'
                  ? 'success'
                  : run.status === 'failed'
                    ? 'error'
                    : 'warning'
              "
              size="sm"
              >{{ run.status }}</UBadge
            >
            <span class="wf-run-name">{{
              run.workflow_name || run.workflow_id
            }}</span>
            <span class="wf-run-time">{{
              new Date(run.started_at).toLocaleTimeString()
            }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from "vue";
import UIcon from "../../../skills/atoms/UIcon.vue";
import UBadge from "../../../skills/atoms/UBadge.vue";
import UButton from "../../../skills/atoms/UButton.vue";
import { useWorkflowStore } from "../../../stores/workflow";
import { SNACKBAR_BASE } from "../../../api/base";

const wf = useWorkflowStore();

// ── Types ──────────────────────────────────────────────────────

interface AutomationStatus {
  engine: { available: boolean; path: string | null; udev_dir: string };
  git_branch: string;
  knowledge_root: string;
  notebook_count: number;
  notebooks: NotebookEntry[];
}

interface NotebookEntry {
  name: string;
  path: string;
  size: number;
  mtime: number;
}

interface NotebookCell {
  id: string;
  type: "code" | "markdown";
  source: string;
  output: string;
  error: boolean;
  running: boolean;
}

// ── State ──────────────────────────────────────────────────────

const status = ref<AutomationStatus | null>(null);
const notebooks = ref<NotebookEntry[]>([]);
const output = ref("");
const outputOk = ref(true);
const running = ref(false);
const loading = ref(false);

// Notebook editor state
const activeNotebook = ref<NotebookEntry | null>(null);
const cells = ref<NotebookCell[]>([]);
const runningAll = ref(false);

const engineAvailable = computed(
  () => status.value?.engine?.available ?? false,
);

let cellCounter = 0;
function nextCellId(): string {
  return `cell-${Date.now()}-${++cellCounter}`;
}

// ── Backend API ────────────────────────────────────────────────

async function loadStatus() {
  loading.value = true;
  try {
    const res = await fetch(`${SNACKBAR_BASE}/api/automation/status`);
    if (res.ok) {
      const data = (await res.json()) as AutomationStatus;
      status.value = data;
      notebooks.value = data.notebooks || [];
    }
  } catch (e) {
    console.warn("Automation status fetch failed:", e);
  } finally {
    loading.value = false;
  }
}

async function runPipeline(dryRun: boolean) {
  running.value = true;
  output.value = "";
  try {
    const res = await fetch(`${SNACKBAR_BASE}/api/automation/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ dry_run: dryRun }),
    });
    const text = await res.text();
    output.value = text;
    outputOk.value = res.ok;
    if (res.ok) await loadStatus();
  } catch (e: any) {
    output.value = e?.message || "Pipeline request failed";
    outputOk.value = false;
  } finally {
    running.value = false;
  }
}

// ── Notebook Editor ────────────────────────────────────────────

function createNotebook() {
  const name = `notebook-${new Date().toISOString().slice(0, 10)}.ipynb`;
  activeNotebook.value = {
    name,
    path: name,
    size: 0,
    mtime: Date.now() / 1000,
  };
  cells.value = [
    {
      id: nextCellId(),
      type: "code",
      source: "",
      output: "",
      error: false,
      running: false,
    },
  ];
}

async function openNotebookEditor(nb: NotebookEntry) {
  activeNotebook.value = nb;
  try {
    const res = await fetch(
      `${SNACKBAR_BASE}/api/automation/notebooks/markdown?path=${encodeURIComponent(nb.path)}`,
    );
    if (res.ok) {
      const text = await res.text();
      cells.value = parseCells(text);
    } else {
      cells.value = [
        {
          id: nextCellId(),
          type: "code",
          source: "",
          output: "",
          error: false,
          running: false,
        },
      ];
    }
  } catch {
    cells.value = [
      {
        id: nextCellId(),
        type: "code",
        source: "",
        output: "",
        error: false,
        running: false,
      },
    ];
  }
}

function closeNotebook() {
  activeNotebook.value = null;
  cells.value = [];
}

function parseCells(text: string): NotebookCell[] {
  const cellBlocks = text.split(/(?=^```|^# %%|^# In\[)/m);
  return cellBlocks
    .filter((b) => b.trim())
    .map((block) => {
      const isMd =
        block.startsWith("```") || !block.trimStart().startsWith("#");
      const source = block
        .replace(/^```\w*\n?/, "")
        .replace(/\n?```$/, "")
        .replace(/^# %%\n?/m, "")
        .replace(/^# In\[\d+\]\n?/m, "")
        .trim();
      return {
        id: nextCellId(),
        type:
          isMd &&
          !block.includes("import ") &&
          !block.includes("def ") &&
          !block.includes("print(")
            ? "markdown"
            : "code",
        source,
        output: "",
        error: false,
        running: false,
      };
    });
}

function addCell(type: "code" | "markdown") {
  cells.value.push({
    id: nextCellId(),
    type,
    source: "",
    output: "",
    error: false,
    running: false,
  });
}

function deleteCell(idx: number) {
  if (cells.value.length <= 1) return;
  cells.value.splice(idx, 1);
}

function toggleCellType(idx: number) {
  const cell = cells.value[idx];
  if (!cell) return;
  cell.type = cell.type === "code" ? "markdown" : "code";
}

async function runCell(idx: number) {
  const cell = cells.value[idx];
  if (!cell || cell.type !== "code") return;

  cell.running = true;
  cell.error = false;
  try {
    const res = await fetch(
      `${SNACKBAR_BASE}/api/automation/research/generate`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: cell.source, format: "python" }),
      },
    );
    const text = await res.text();
    cell.output = text;
    cell.error = !res.ok;
  } catch (e: any) {
    cell.output = e?.message || "Cell execution failed";
    cell.error = true;
  } finally {
    cell.running = false;
  }
}

async function runAllCells() {
  runningAll.value = true;
  for (let i = 0; i < cells.value.length; i++) {
    if (cells.value[i].type === "code") {
      await runCell(i);
    }
  }
  runningAll.value = false;
}

async function saveNotebook() {
  if (!activeNotebook.value) return;
  const md = cells.value
    .map((c) => (c.type === "code" ? `# %%\n${c.source}\n` : `${c.source}\n`))
    .join("\n");
  try {
    await fetch(`${SNACKBAR_BASE}/api/automation/notebooks/publish`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        path: activeNotebook.value.path,
        content: md,
      }),
    });
  } catch (e) {
    console.warn("Notebook save failed:", e);
  }
}

function openNotebook(nb: NotebookEntry) {
  window.open(
    `${SNACKBAR_BASE}/api/automation/notebooks/markdown?path=${encodeURIComponent(nb.path)}`,
    "_blank",
  );
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(ts: number): string {
  return new Date(ts * 1000).toLocaleDateString();
}

onMounted(() => {
  loadStatus();
});
</script>

<style scoped>
.wf-panel {
  display: flex;
  flex-direction: row;
  gap: 0;
  min-height: 0;
  flex: 1;
  overflow: hidden;
}

.wf-panel__main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-md);
  overflow-y: auto;
}

.wf-automation-missing {
  padding: var(--usx-spacing-md);
  border-radius: var(--usx-radius-md);
  background: color-mix(in srgb, var(--usx-color-warning) 10%, transparent);
  color: var(--usx-color-warning);
  font-size: var(--usx-font-size-sm);
}

.wf-automation-actions {
  display: flex;
  gap: var(--usx-spacing-sm);
  flex-wrap: wrap;
}

.wf-automation-output {
  padding: var(--usx-spacing-md);
  background: var(--usx-color-surface-variant);
  border-radius: var(--usx-radius-md);
  border: var(--usx-border-width) solid var(--usx-color-border);
  overflow: auto;
  max-height: 12rem;
}

.wf-automation-output pre {
  margin: 0;
  font-family: var(--usx-font-family-mono);
  font-size: var(--usx-font-size-xs);
  white-space: pre-wrap;
}

.wf-automation-output--error {
  border-color: var(--usx-color-danger);
}

/* ── Notebook editor ─────────────────────────────────────────── */

.nb-editor {
  display: flex;
  flex-direction: column;
  gap: 0;
  flex: 1;
  min-height: 0;
}

.nb-editor__toolbar {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md) var(--usx-radius-md) 0 0;
  background: var(--usx-color-surface);
  flex-shrink: 0;
}

.nb-editor__title {
  flex: 1;
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-semibold);
  font-family: var(--usx-font-family-mono);
  color: var(--usx-color-on-surface);
}

.nb-editor__cells {
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  border-left: var(--usx-border-width) solid var(--usx-color-border);
  border-right: var(--usx-border-width) solid var(--usx-color-border);
}

.nb-cell {
  display: flex;
  gap: 0;
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
  background: var(--usx-color-background);
  min-height: 0;
}

.nb-cell__gutter {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-sm) var(--usx-spacing-sm);
  background: var(--usx-color-surface-variant);
  border-right: var(--usx-border-width) solid var(--usx-color-border);
  width: 4ch;
  flex-shrink: 0;
}

.nb-cell__index {
  font-family: var(--usx-font-family-mono);
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
}

.nb-cell__run-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border: var(--usx-border-width) solid var(--usx-color-primary);
  border-radius: var(--usx-radius-sm);
  background: transparent;
  color: var(--usx-color-primary);
  cursor: pointer;
  padding: 0;
  min-height: 0;
}

.nb-cell__run-btn:hover {
  background: var(--usx-color-primary);
  color: var(--usx-color-on-primary, #fff);
}

.nb-cell__body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.nb-cell__input {
  width: 100%;
  border: none;
  background: transparent;
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  font-family: var(--usx-font-family-mono);
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface);
  resize: vertical;
  outline: none;
}

.nb-cell__input--md {
  font-family: var(--usx-font-family-sans);
}

.nb-cell__output {
  border-top: var(--usx-border-width) solid var(--usx-color-border);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  background: var(--usx-color-surface-variant);
  overflow: auto;
  max-height: 16rem;
}

.nb-cell__output pre {
  margin: 0;
  font-family: var(--usx-font-family-mono);
  font-size: var(--usx-font-size-xs);
  white-space: pre-wrap;
}

.nb-cell__output--error {
  background: color-mix(in srgb, var(--usx-color-danger) 6%, transparent);
  color: var(--usx-color-danger);
}

.nb-cell__actions {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: var(--usx-spacing-xs);
  flex-shrink: 0;
}

.nb-cell__type-btn,
.nb-cell__del-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border: none;
  background: transparent;
  color: var(--usx-color-on-surface-muted);
  cursor: pointer;
  padding: 0;
  border-radius: var(--usx-radius-sm);
  min-height: 0;
}

.nb-cell__type-btn:hover,
.nb-cell__del-btn:hover {
  background: var(--usx-color-surface-variant);
  color: var(--usx-color-on-surface);
}

.nb-cell__del-btn:hover {
  color: var(--usx-color-danger);
}

.nb-editor__add-bar {
  display: flex;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-top: none;
  border-radius: 0 0 var(--usx-radius-md) var(--usx-radius-md);
  background: var(--usx-color-surface);
}

.nb-add-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border: var(--usx-border-width) dashed var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: transparent;
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
  cursor: pointer;
  min-height: 0;
}

.nb-add-btn:hover {
  border-color: var(--usx-color-primary);
  color: var(--usx-color-primary);
}

/* ── Notebooks list ──────────────────────────────────────────── */

.wf-automation-empty {
  padding: var(--usx-spacing-lg);
  text-align: center;
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
}

.wf-automation-notebooks {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
}

.wf-automation-notebook-list {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
}

/* 2‑col notebook list on wide screens */
@media (min-width: 1100px) {
  .wf-automation-notebook-list {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--usx-spacing-xs);
  }
}

.wf-automation-notebook-row {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  background: var(--usx-color-surface);
  border-radius: var(--usx-radius-sm);
  border: var(--usx-border-width) solid var(--usx-color-border);
  cursor: pointer;
}

.wf-automation-notebook-row:hover {
  border-color: var(--usx-color-primary);
}

.wf-automation-notebook-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.wf-automation-notebook-name {
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-semibold);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.wf-automation-notebook-path {
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
  font-family: var(--usx-font-family-mono);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.wf-automation-notebook-meta {
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
  white-space: nowrap;
}

/* ── Back button reuse ───────────────────────────────────────── */

.wf-editor-back-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  font-size: var(--usx-font-size-sm);
  cursor: pointer;
  min-height: 0;
}

.wf-editor-back-btn:hover {
  background: color-mix(in srgb, var(--usx-color-primary) 8%, transparent);
}

/* ── Run log ────────────────────────────────────────────────── */

.wf-section {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
}

.wf-section-title {
  font-size: var(--usx-font-size-xs);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface-muted);
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.wf-run-row {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  background: var(--usx-color-surface);
  border-radius: var(--usx-radius-sm);
  border: var(--usx-border-width) solid var(--usx-color-border);
  font-size: var(--usx-font-size-sm);
}

.wf-run-name {
  flex: 1;
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.wf-run-time {
  font-family: var(--usx-font-family-mono);
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
}
</style>

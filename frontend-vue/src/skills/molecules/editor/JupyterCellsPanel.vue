/**
 * @component JupyterCellsPanel
 * @description Notebook cell editor with per-cell CodeMirror instances.
 * Supports code (syntax-highlighted) and markdown cell types.
 */
<template>
  <div class="nb-cells-panel">
    <div class="nb-cells-panel__scroll">
      <div v-if="cells.length === 0" class="nb-cells-panel__empty">
        No cells. Click <strong>+ Code</strong> or <strong>+ Markdown</strong> below.
      </div>
      <div v-for="(cell, idx) in cells" :key="cell.id" class="nb-cell">
        <div class="nb-cell__gutter">
          <span class="nb-cell__index">[{{ idx + 1 }}]</span>
        </div>
        <div class="nb-cell__body">
          <div v-if="cell.type === 'code'" class="nb-cell__code">
            <div :ref="(el) => assignCellRef(el as HTMLElement, cell.id)" class="nb-cell__editor" />
          </div>
          <div v-else class="nb-cell__md">
            <textarea
              v-model="cell.source"
              class="nb-cell__textarea"
              :rows="cell.source.split('\n').length || 2"
              placeholder="Markdown content..."
              @input="onCellChange(idx, ($event.target as HTMLTextAreaElement).value)"
            />
          </div>
        </div>
        <div class="nb-cell__actions">
          <button class="nb-cell__btn" :title="cell.type === 'code' ? 'Switch to Markdown' : 'Switch to Code'"
            @click="toggleCellType(idx)">
            <UIcon :name="cell.type === 'code' ? 'article' : 'code'" :size="14" />
          </button>
          <button class="nb-cell__btn nb-cell__btn--danger" title="Delete cell" @click="$emit('delete-cell', idx)">
            <UIcon name="close" :size="14" />
          </button>
        </div>
      </div>
    </div>
    <div class="nb-cells-panel__footer">
      <button class="nb-cells-panel__add-btn" @click="$emit('add-cell', 'code')">
        <UIcon name="add" :size="14" /> Code
      </button>
      <button class="nb-cells-panel__add-btn" @click="$emit('add-cell', 'markdown')">
        <UIcon name="add" :size="14" /> Markdown
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from "vue";
import { EditorState } from "@codemirror/state";
import { EditorView, keymap, lineNumbers } from "@codemirror/view";
import { syntaxHighlighting, defaultHighlightStyle } from "@codemirror/language";
import { defaultKeymap, history, historyKeymap } from "@codemirror/commands";
import { oneDark } from "@codemirror/theme-one-dark";
import UIcon from "../../atoms/UIcon.vue";
import { loadLanguage, languageFor } from "./codeLanguages";

export interface NotebookCell {
  id: string;
  type: "code" | "markdown";
  source: string;
  language?: string;
}

const props = defineProps<{
  cells: NotebookCell[];
  defaultLanguage?: string;
}>();

const emit = defineEmits<{
  "update:cell-source": [idx: number, source: string];
  "toggle-cell-type": [idx: number];
  "add-cell": [type: "code" | "markdown"];
  "delete-cell": [idx: number];
}>();

const cellEditors = new Map<string, EditorView>();
const cellRefs = new Map<string, HTMLElement>();

function assignCellRef(el: HTMLElement | null, cellId: string) {
  if (el && !cellRefs.has(cellId)) {
    cellRefs.set(cellId, el);
    createCellEditor(cellId);
  }
}

function onCellChange(idx: number, value: string) {
  emit("update:cell-source", idx, value);
}

function toggleCellType(idx: number) {
  emit("toggle-cell-type", idx);
}

async function createCellEditor(cellId: string) {
  const host = cellRefs.get(cellId);
  if (!host) return;
  const cell = props.cells.find((c) => c.id === cellId);
  if (!cell || cell.type !== "code") return;

  if (cellEditors.has(cellId)) {
    cellEditors.get(cellId)!.destroy();
    cellEditors.delete(cellId);
  }

  const lang = cell.language || props.defaultLanguage || "python";
  const langExt = await loadLanguage(languageFor(lang));

  const theme = EditorView.theme({
    "&": { fontSize: "var(--usx-font-size-sm, 13px)", background: "var(--usx-color-background, #0d1117)", color: "var(--usx-color-on-surface, #c9d1d9)" },
    ".cm-scroller": { overflow: "auto" },
    ".cm-content": { padding: "var(--usx-spacing-sm, 8px)", fontFamily: 'var(--usx-font-family-mono, "SF Mono", monospace)' },
    ".cm-gutters": { display: "none" },
    "&.cm-focused": { outline: "none" },
  }, { dark: true });

  const view = new EditorView({
    parent: host,
    state: EditorState.create({
      doc: cell.source,
      extensions: [
        history(),
        keymap.of([...defaultKeymap, ...historyKeymap]),
        lineNumbers(),
        langExt ?? [],
        syntaxHighlighting(defaultHighlightStyle, { fallback: true }),
        oneDark,
        theme,
        EditorView.updateListener.of((update) => {
          if (update.docChanged) {
            const idx = props.cells.findIndex((c) => c.id === cellId);
            if (idx >= 0) {
              emit("update:cell-source", idx, update.state.doc.toString());
            }
          }
        }),
      ],
    }),
  });

  cellEditors.set(cellId, view);
}

function destroyCellEditor(cellId: string) {
  const editor = cellEditors.get(cellId);
  if (editor) {
    editor.destroy();
    cellEditors.delete(cellId);
  }
  cellRefs.delete(cellId);
}

watch(
  () => props.cells,
  (newCells, oldCells) => {
    const newIds = new Set(newCells.map((c) => c.id));
    // Destroy editors for removed cells
    for (const [id] of cellEditors) {
      if (!newIds.has(id)) destroyCellEditor(id);
    }
    // Create editors for new code cells
    nextTick(() => {
      for (const cell of newCells) {
        if (cell.type === "code" && !cellEditors.has(cell.id)) {
          const host = cellRefs.get(cell.id);
          if (host) createCellEditor(cell.id);
        }
      }
    });
  },
  { deep: true },
);

onBeforeUnmount(() => {
  for (const [id] of cellEditors) destroyCellEditor(id);
});
</script>

<style scoped>
.nb-cells-panel {
  display: flex; flex-direction: column; height: 100%; min-height: 0; overflow: hidden;
}
.nb-cells-panel__scroll {
  flex: 1; overflow-y: auto; min-height: 0;
}
.nb-cells-panel__empty {
  padding: var(--usx-spacing-lg); text-align: center;
  color: var(--usx-color-on-surface-muted); font-size: var(--usx-font-size-sm);
}
.nb-cell {
  display: flex; border-bottom: var(--usx-border-width) solid var(--usx-color-border);
}
.nb-cell__gutter {
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  background: var(--usx-color-surface-variant);
  border-right: var(--usx-border-width) solid var(--usx-color-border);
  width: 3.5ch; flex-shrink: 0; display: flex; align-items: flex-start;
  justify-content: center; padding-top: var(--usx-spacing-sm);
}
.nb-cell__index {
  font-family: var(--usx-font-family-mono); font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
}
.nb-cell__body { flex: 1; min-width: 0; }
.nb-cell__code { min-height: 3em; }
.nb-cell__editor { min-height: 3em; }
.nb-cell__textarea {
  width: 100%; border: none; background: transparent;
  padding: var(--usx-spacing-sm); font-family: var(--usx-font-family-sans);
  font-size: var(--usx-font-size-sm); resize: vertical; outline: none;
  color: var(--usx-color-on-surface);
}
.nb-cell__actions {
  display: flex; flex-direction: column; gap: 2px; padding: var(--usx-spacing-xs);
}
.nb-cell__btn {
  display: flex; align-items: center; justify-content: center;
  width: 20px; height: 20px; border: none; background: transparent;
  color: var(--usx-color-on-surface-muted); cursor: pointer; min-height: 0;
}
.nb-cell__btn:hover { color: var(--usx-color-primary); }
.nb-cell__btn--danger:hover { color: var(--usx-color-danger); }
.nb-cells-panel__footer {
  display: flex; gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border-top: var(--usx-border-width) solid var(--usx-color-border);
  background: var(--usx-color-surface); flex-shrink: 0;
}
.nb-cells-panel__add-btn {
  display: inline-flex; align-items: center; gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border: var(--usx-border-width) dashed var(--usx-color-border);
  border-radius: var(--usx-radius-sm); background: transparent;
  color: var(--usx-color-on-surface-muted); font-size: var(--usx-font-size-sm);
  cursor: pointer; min-height: 0;
}
.nb-cells-panel__add-btn:hover {
  border-color: var(--usx-color-primary); color: var(--usx-color-primary);
}
</style>

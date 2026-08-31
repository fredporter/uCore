/**
 * @component DiffEditorPanel
 * @description Side-by-side diff view using @codemirror/merge.
 * Left panel shows original, right shows modified, with gutter change indicators.
 */
<template>
  <div class="diff-editor-panel">
    <div class="diff-editor-panel__header">
      <span class="diff-editor-panel__label diff-editor-panel__label--original">
        {{ baselineLabel }}
      </span>
      <span class="diff-editor-panel__label diff-editor-panel__label--modified">
        {{ hasRepositoryDiff ? "Working copy" : "No repository changes" }}
      </span>
    </div>
    <div ref="mergeHost" class="diff-editor-panel__merge" />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onBeforeUnmount, watch } from "vue";
import { EditorState } from "@codemirror/state";
import { EditorView } from "@codemirror/view";
import { MergeView } from "@codemirror/merge";
import { oneDark } from "@codemirror/theme-one-dark";

interface Props {
  original: string;
  modified: string;
  status?: "clean" | "modified" | "added" | "deleted";
  hasRepositoryDiff?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  status: "clean",
  hasRepositoryDiff: false,
});

const emit = defineEmits<{
  "update:modified": [value: string];
}>();

const mergeHost = ref<HTMLDivElement | null>(null);
let mergeView: MergeView | null = null;
const baselineLabel = computed(() => {
  if (props.status === "added") return "New file";
  if (props.status === "modified") return "Git baseline";
  if (props.status === "deleted") return "Deleted in repository";
  return "Git baseline";
});

onMounted(() => {
  if (!mergeHost.value) return;

  mergeView = new MergeView({
    a: {
      doc: props.original,
      extensions: [
        EditorState.readOnly.of(true),
        EditorView.editable.of(false),
        oneDark,
        EditorView.theme({
          "&": {
            background: "var(--usx-color-background)",
            color: "var(--usx-color-on-surface)",
            fontSize: "var(--usx-font-size-sm)",
            height: "100%",
          },
          ".cm-scroller": { overflow: "auto" },
          ".cm-content": {
            padding: "var(--usx-spacing-xs)",
          },
        }),
      ],
    },
    b: {
      doc: props.modified,
      extensions: [
        oneDark,
        EditorView.theme({
          "&": {
            background: "var(--usx-color-background)",
            color: "var(--usx-color-on-surface)",
            fontSize: "var(--usx-font-size-sm)",
            height: "100%",
          },
          ".cm-scroller": { overflow: "auto" },
          ".cm-content": {
            padding: "var(--usx-spacing-xs)",
          },
        }),
        EditorView.updateListener.of((update) => {
          if (update.docChanged) {
            emit("update:modified", update.state.doc.toString());
          }
        }),
      ],
    },
    parent: mergeHost.value,
    revertControls: "a-to-b",
  });
});

onBeforeUnmount(() => {
  mergeView?.destroy();
  mergeView = null;
});

watch(
  () => props.original,
  (val) => {
    if (!mergeView) return;
    const current = mergeView.a.state.doc.toString();
    if (current !== val) {
      mergeView.a.dispatch({
        changes: {
          from: 0,
          to: mergeView.a.state.doc.length,
          insert: val,
        },
      });
    }
  },
);

watch(
  () => props.modified,
  (val) => {
    if (!mergeView) return;
    const current = mergeView.b.state.doc.toString();
    if (current !== val) {
      mergeView.b.dispatch({
        changes: {
          from: 0,
          to: mergeView.b.state.doc.length,
          insert: val,
        },
      });
    }
  },
);

defineExpose({ mergeView: () => mergeView });
</script>

<style scoped>
.diff-editor-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

.diff-editor-panel__header {
  display: flex;
  flex-shrink: 0;
}

.diff-editor-panel__label {
  flex: 1;
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  font-size: var(--usx-font-size-xs);
  font-weight: var(--usx-font-weight-semibold);
  text-align: center;
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
}

.diff-editor-panel__label--original {
  background: color-mix(in srgb, var(--usx-color-danger) 8%, transparent);
  color: var(--usx-color-danger);
  border-right: var(--usx-border-width) solid var(--usx-color-border);
}

.diff-editor-panel__label--modified {
  background: color-mix(in srgb, var(--usx-color-success) 8%, transparent);
  color: var(--usx-color-success);
}

.diff-editor-panel__merge {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.diff-editor-panel__merge :deep(.cm-mergeView) {
  height: 100%;
}

.diff-editor-panel__merge :deep(.cm-mergeViewEditor) {
  height: 100%;
}

.diff-editor-panel__merge :deep(.cm-mergeViewEditor .cm-editor) {
  height: 100%;
}
</style>

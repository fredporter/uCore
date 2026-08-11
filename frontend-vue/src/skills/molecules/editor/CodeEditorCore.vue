/**
 * @component CodeEditorCore
 * @description Reusable single-panel CodeMirror 6 editor wrapper.
 * Handles language detection, theming, read-only toggle, and v-model binding.
 */
<template>
  <div ref="hostEl" class="code-editor-core" />
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount } from "vue";
import { Compartment, EditorState } from "@codemirror/state";
import type { Extension } from "@codemirror/state";
import {
  EditorView, keymap, placeholder as placeholderExt, lineNumbers,
  highlightActiveLine, highlightActiveLineGutter,
  drawSelection, dropCursor, highlightSpecialChars,
  rectangularSelection, crosshairCursor,
} from "@codemirror/view";
import {
  defaultKeymap, history, historyKeymap, indentWithTab,
} from "@codemirror/commands";
import {
  bracketMatching, foldGutter, indentOnInput,
  syntaxHighlighting, defaultHighlightStyle,
} from "@codemirror/language";
import { closeBrackets, closeBracketsKeymap } from "@codemirror/autocomplete";
import { searchKeymap, highlightSelectionMatches } from "@codemirror/search";
import { oneDark } from "@codemirror/theme-one-dark";
import { loadLanguage, languageFor } from "./codeLanguages";

// ── Props ────────────────────────────────────────────────────────────

interface Props {
  modelValue?: string; filename?: string; language?: string;
  readOnly?: boolean; placeholder?: string;
  showLineNumbers?: boolean; showFoldGutter?: boolean;
  showActiveLine?: boolean; enableSearch?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: "", filename: "", language: "", readOnly: false,
  placeholder: "Start editing...", showLineNumbers: true,
  showFoldGutter: true, showActiveLine: true, enableSearch: true,
});

const emit = defineEmits<{
  "update:modelValue": [value: string]; change: [value: string];
  save: [value: string]; focus: []; blur: [];
  "language-ready": [lang: string];
}>();

// ── State ─────────────────────────────────────────────────────────────

const hostEl = ref<HTMLDivElement | null>(null);
const detectedLanguage = ref("markdown");
const languageReady = ref(false);
const languageCompartment = new Compartment();
const readOnlyCompartment = new Compartment();
let editorView: EditorView | null = null;

// ── Theme ─────────────────────────────────────────────────────────────

const baseTheme = EditorView.theme(
  {
    "&": {
      height: "100%",
      width: "100%",
      background: "var(--usx-color-background, #0d1117)",
      color: "var(--usx-color-on-surface, #c9d1d9)",
      fontSize: "var(--usx-font-size-sm, 13px)",
      lineHeight: "1.6",
    },
    ".cm-scroller": {
      overflow: "auto",
      fontFamily:
        'var(--usx-font-family-mono, "SF Mono", "Fira Code", monospace)',
    },
    ".cm-content": {
      padding: "var(--usx-spacing-sm, 8px) 0",
      caretColor: "var(--usx-color-primary, #58a6ff)",
    },
    "&.cm-focused": { outline: "none" },
    "&.cm-focused .cm-selectionBackground, ::selection": {
      backgroundColor:
        "color-mix(in srgb, var(--usx-color-primary, #58a6ff) 25%, transparent) !important",
    },
    ".cm-gutters": {
      background: "var(--usx-color-surface-variant, #161b22)",
      borderRight:
        "var(--usx-border-width, 1px) solid var(--usx-color-border, #30363d)",
      color: "var(--usx-color-on-surface-muted, #484f58)",
    },
    ".cm-activeLineGutter": {
      backgroundColor:
        "color-mix(in srgb, var(--usx-color-primary, #58a6ff) 8%, transparent)",
      color: "var(--usx-color-on-surface, #c9d1d9)",
    },
    ".cm-activeLine": { backgroundColor: "transparent" },
    ".cm-cursor, .cm-dropCursor": {
      borderLeftColor: "var(--usx-color-primary, #58a6ff)",
    },
    ".cm-matchingBracket": {
      backgroundColor:
        "color-mix(in srgb, var(--usx-color-primary, #58a6ff) 18%, transparent)",
      outline: "1px solid var(--usx-color-border, #30363d)",
      color: "var(--usx-color-primary, #58a6ff)",
    },
    ".cm-foldPlaceholder": {
      background: "var(--usx-color-surface-variant, #161b22)",
      border:
        "var(--usx-border-width, 1px) solid var(--usx-color-border, #30363d)",
      color: "var(--usx-color-on-surface-muted, #484f58)",
    },
    ".cm-tooltip": {
      background: "var(--usx-color-surface, #0d1117)",
      border:
        "var(--usx-border-width, 1px) solid var(--usx-color-border, #30363d)",
      color: "var(--usx-color-on-surface, #c9d1d9)",
    },
    ".cm-searchMatch": {
      backgroundColor:
        "color-mix(in srgb, var(--usx-color-warning, #d29922) 35%, transparent)",
    },
    ".cm-searchMatch-selected": {
      backgroundColor:
        "color-mix(in srgb, var(--usx-color-warning, #d29922) 55%, transparent)",
    },
  },
  { dark: true },
);

// ── Build extensions ──────────────────────────────────────────────────

async function buildExtensions(): Promise<Extension[]> {
  const lang = props.language || languageFor(props.filename || "");
  detectedLanguage.value = lang;
  const languageExt = await loadLanguage(lang);

  const extensions: Extension[] = [
    history(),
    keymap.of([
      ...defaultKeymap,
      ...historyKeymap,
      ...closeBracketsKeymap,
      indentWithTab,
      {
        key: "Mod-s",
        run: () => {
          emit("save", editorView?.state.doc.toString() ?? "");
          return true;
        },
      },
    ]),
    lineNumbers(),
    highlightActiveLine(),
    bracketMatching(),
    closeBrackets(),
    indentOnInput(),
    drawSelection(),
    dropCursor(),
    highlightSpecialChars(),
    rectangularSelection(),
    crosshairCursor(),
    highlightSelectionMatches(),
    props.showFoldGutter ? foldGutter() : [],
    props.showActiveLine ? highlightActiveLineGutter() : [],
    ...(props.enableSearch ? [keymap.of(searchKeymap)] : []),
    placeholderExt(props.placeholder),
    syntaxHighlighting(defaultHighlightStyle, { fallback: true }),
    oneDark,
    baseTheme,
    languageCompartment.of(languageExt ?? []),
    readOnlyCompartment.of(EditorView.editable.of(!props.readOnly)),
    EditorView.updateListener.of((update) => {
      if (update.docChanged) {
        const value = update.state.doc.toString();
        emit("update:modelValue", value);
        emit("change", value);
      }
      if (update.focusChanged) {
        editorView?.hasFocus ? emit("focus") : emit("blur");
      }
    }),
  ];
  return extensions;
}

// ── Public API ────────────────────────────────────────────────────────

function getValue(): string {
  return editorView?.state.doc.toString() ?? props.modelValue;
}

function setValue(value: string) {
  if (!editorView) return;
  const current = editorView.state.doc.toString();
  if (current === value) return;
  editorView.dispatch({
    changes: {
      from: 0, to: editorView.state.doc.length, insert: value,
    },
  });
}

function focus() { editorView?.focus(); }

function getCursorPosition(): { line: number; col: number } {
  if (!editorView) return { line: 1, col: 1 };
  const pos = editorView.state.selection.main.head;
  const line = editorView.state.doc.lineAt(pos);
  return { line: line.number, col: pos - line.from + 1 };
}

function getLineCount(): number {
  return editorView?.state.doc.lines ?? 0;
}

// ── Watchers ──────────────────────────────────────────────────────────

watch(
  () => props.modelValue,
  (newVal) => {
    if (!editorView) return;
    const current = editorView.state.doc.toString();
    if (current !== newVal) setValue(newVal);
  },
);

watch(
  () => props.language || props.filename,
  async () => {
    if (!editorView) return;
    const lang = props.language || languageFor(props.filename || "");
    if (lang !== detectedLanguage.value) {
      detectedLanguage.value = lang;
      const languageExt = await loadLanguage(lang);
      editorView.dispatch({
        effects: languageCompartment.reconfigure(languageExt ?? []),
      });
      emit("language-ready", lang);
    }
  },
);

watch(
  () => props.readOnly,
  () => {
    if (!editorView) return;
    editorView.dispatch({
      effects: readOnlyCompartment.reconfigure(
        EditorView.editable.of(!props.readOnly),
      ),
    });
  },
);

// ── Lifecycle ─────────────────────────────────────────────────────────

onMounted(async () => {
  if (!hostEl.value) return;
  const extensions = await buildExtensions();
  editorView = new EditorView({
    parent: hostEl.value,
    state: EditorState.create({
      doc: props.modelValue,
      extensions,
    }),
  });
  languageReady.value = true;
  emit("language-ready", detectedLanguage.value);
});

onBeforeUnmount(() => {
  editorView?.destroy();
  editorView = null;
});

defineExpose({
  getValue,
  setValue,
  focus,
  getCursorPosition,
  getLineCount,
  editorView: () => editorView,
});

</script>

<style scoped>
.code-editor-core {
  width: 100%;
  height: 100%;
  min-height: 0;
  overflow: hidden;
  display: flex;
}

.code-editor-core :deep(.cm-editor) {
  height: 100%;
  width: 100%;
}

.code-editor-core :deep(.cm-scroller) {
  overflow: auto;
}

.code-editor-core :deep(.cm-placeholder) {
  color: var(--usx-color-on-surface-muted, #484f58);
  font-style: italic;
}
</style>


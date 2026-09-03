<template>
  <div class="markdown-editor">
    <!-- Toolbar: formatting buttons (prose + editable only) plus a slot for
         external controls (save, view mode, close) injected by the parent -->
    <div class="markdown-editor__toolbar">
      <EnhancedBangleToolbar v-if="!readOnly" @command="handleToolbarCommand">
        <template #actions><slot name="toolbar-actions" /></template>
      </EnhancedBangleToolbar>
      <slot v-else name="toolbar-actions" />
    </div>

    <!-- Raw markdown code editor (preserves line breaks) -->
    <textarea
      v-if="editMode === 'code'"
      ref="codeEl"
      class="markdown-editor__code"
      :value="modelValue"
      :readonly="readOnly"
      spellcheck="false"
      @input="onCodeInput"
      @keydown="onEditorKeydown"
    />

    <!-- ProseMirror WYSIWYG editor -->
    <div
      v-else
      ref="editorEl"
      class="markdown-editor__host"
      :class="{ 'markdown-editor__host--readonly': readOnly }"
      @keydown="onEditorKeydown"
    />
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import "@bangle.dev/core/style.css";
import {
  BangleEditor as MarkdownRuntime,
  BangleEditorState,
} from "@bangle.dev/core";
import {
  blockquote,
  bold,
  bulletList,
  code,
  codeBlock,
  doc,
  hardBreak,
  heading,
  history,
  horizontalRule,
  italic,
  link,
  listItem,
  orderedList,
  paragraph,
  strike,
  text,
  underline,
} from "@bangle.dev/base-components";
import { Plugin } from "@bangle.dev/pm";
import { defaultMarkdownSerializer } from "prosemirror-markdown";
import { marked } from "marked";
import DOMPurify from "dompurify";
import EnhancedBangleToolbar, { type EditorCommand } from "./EnhancedBangleToolbar.vue";

interface Props {
  modelValue?: string;
  toolbars?: string[];
  preview?: boolean;
  htmlPreview?: boolean;
  noUpload?: boolean;
  autofocus?: boolean;
  readOnly?: boolean;
  editMode?: "prose" | "code";
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: "",
  toolbars: undefined,
  preview: true,
  htmlPreview: false,
  noUpload: false,
  autofocus: false,
  readOnly: false,
  editMode: "prose",
});

const emit = defineEmits<{
  "update:modelValue": [value: string];
  save: [value: string];
  change: [value: string];
  toolbarAction: [action: "scrape" | "summarize" | "citation" | "copy-binder" | "variant" | "archive" | "outline"];
}>();

const editorEl = ref<HTMLDivElement | null>(null);
const codeEl = ref<HTMLTextAreaElement | null>(null);
const editMode = ref<"prose" | "code">(props.editMode);
let editor: MarkdownRuntime | null = null;
let lastExternalValue = props.modelValue;

function docToMarkdown(editor: MarkdownRuntime): string {
  try {
    return defaultMarkdownSerializer.serialize(editor.view.state.doc);
  } catch {
    return "";
  }
}

function createChangePlugin() {
  return new Plugin({
    view: () => ({
      update(view, prevState) {
        if (view.state.doc.eq(prevState.doc)) {
          return;
        }
        const value = defaultMarkdownSerializer.serialize(view.state.doc);
        if (value === lastExternalValue) {
          return;
        }
        emit("update:modelValue", value);
        emit("change", value);
      },
    }),
  });
}

function resolvePlugins(raw: unknown, payload: any): unknown[] {
  if (!raw || raw === false) {
    return [];
  }
  if (typeof raw === "function") {
    return resolvePlugins(raw(payload), payload);
  }
  if (Array.isArray(raw)) {
    return raw.flatMap((item) => resolvePlugins(item, payload));
  }
  return [raw];
}

// ─── Toolbar action handlers ───────────────────────────────
function applyBold() {
  if (editMode.value === "code") return wrapCodeSelection("**", "**", "bold text");
  if (!editor) return;
  bold.commands.toggleBold()(editor.view.state, editor.view.dispatch);
  editor.view.focus();
}

function applyItalic() {
  if (editMode.value === "code") return wrapCodeSelection("_", "_", "italic text");
  if (!editor) return;
  italic.commands.toggleItalic()(editor.view.state, editor.view.dispatch);
  editor.view.focus();
}

function applyUnderline() {
  if (editMode.value === "code") return wrapCodeSelection("<u>", "</u>", "underlined text");
  if (!editor) return;
  underline.commands.toggleUnderline()(editor.view.state, editor.view.dispatch);
  editor.view.focus();
}

function applyCode() {
  if (editMode.value === "code") return wrapCodeSelection("`", "`", "code");
  if (!editor) return;
  code.commands.toggleCode()(editor.view.state, editor.view.dispatch);
  editor.view.focus();
}

function handleToolbarCommand(command: EditorCommand) {
  if (command === "bold") return applyBold();
  if (command === "italic") return applyItalic();
  if (command === "underline") return applyUnderline();
  if (command === "strike") return applyStrike();
  if (command === "code") return applyCode();
  if (command === "link") return applyLink();
  if (command.startsWith("heading-")) return applyHeadingLevel(Number(command.slice(-1)));
  if (command === "blockquote") return applyBlockquote();
  if (command === "bullet-list") return applyBulletList();
  if (command === "ordered-list") return applyOrderedList();
  if (command === "code-block") return insertBlock("```\ncode\n```\n");
  if (command === "horizontal-rule") return insertBlock("---\n");
  if (command === "table") return insertBlock("| Column | Value |\n| --- | --- |\n| Item | Value |\n");
  if (command === "callout") return insertBlock("> [!NOTE]\n> Add a note.\n");
  if (command === "footnote") return insertBlock("Reference[^1]\n\n[^1]: Source details.\n");
  if (command === "undo") return undo();
  if (command === "redo") return redo();
  emit(
    "toolbarAction",
    command as "scrape" | "summarize" | "citation" | "copy-binder" | "variant" | "archive" | "outline",
  );
}

function onEditorKeydown(event: KeyboardEvent) {
  if (props.readOnly || !(event.metaKey || event.ctrlKey)) return;
  const key = event.key.toLowerCase();
  const command = key === "b"
    ? "bold"
    : key === "i"
      ? "italic"
      : key === "u"
        ? "underline"
        : key === "k"
          ? "link"
          : key === "z" && event.shiftKey
            ? "redo"
            : key === "z"
              ? "undo"
              : null;
  if (!command) return;
  event.preventDefault();
  handleToolbarCommand(command);
}

function applyStrike() {
  if (editMode.value === "code") return wrapCodeSelection("~~", "~~", "struck text");
  if (!editor) return;
  strike.commands.toggleStrike()(editor.view.state, editor.view.dispatch);
  editor.view.focus();
}

function applyLink() {
  if (editMode.value === "code") return wrapCodeSelection("[", "](https://example.com)", "link text");
  emit("toolbarAction", "citation");
}

function applyHeadingLevel(level: number) {
  if (editMode.value === "code") return prefixCodeLines(`${"#".repeat(level)} `);
  if (!editor) return;
  heading.commands.toggleHeading(level)(editor.view.state, editor.view.dispatch);
  editor.view.focus();
}

function insertBlock(snippet: string) {
  if (editMode.value === "code") return insertCodeSnippet(snippet);
  const value = `${currentValue().replace(/\s*$/, "")}\n\n${snippet}`;
  lastExternalValue = value;
  emit("update:modelValue", value);
  emit("change", value);
}

function insertCodeSnippet(snippet: string) {
  const el = codeEl.value;
  if (!el) return;
  const start = el.selectionStart;
  const value = `${props.modelValue.slice(0, start)}${snippet}${props.modelValue.slice(el.selectionEnd)}`;
  commitCodeEdit(value, start, start + snippet.length);
}

function applyBlockquote() {
  if (editMode.value === "code") return prefixCodeLines("> ");
  if (!editor) return;
  blockquote.commands.wrapInBlockquote()(
    editor.view.state,
    editor.view.dispatch,
  );
  editor.view.focus();
}

function applyBulletList() {
  if (editMode.value === "code") return prefixCodeLines("- ");
  if (!editor) return;
  bulletList.commands.toggleBulletList()(
    editor.view.state,
    editor.view.dispatch,
  );
  editor.view.focus();
}

function applyOrderedList() {
  if (editMode.value === "code") return prefixCodeLines("1. ");
  if (!editor) return;
  orderedList.commands.toggleOrderedList()(
    editor.view.state,
    editor.view.dispatch,
  );
  editor.view.focus();
}

function undo() {
  if (!editor) return;
  history.commands.undo()(editor.view.state, editor.view.dispatch);
  editor.view.focus();
}

function redo() {
  if (!editor) return;
  history.commands.redo()(editor.view.state, editor.view.dispatch);
  editor.view.focus();
}

function commitCodeEdit(value: string, start: number, end: number) {
  lastExternalValue = value;
  emit("update:modelValue", value);
  emit("change", value);
  requestAnimationFrame(() => {
    codeEl.value?.focus();
    codeEl.value?.setSelectionRange(start, end);
  });
}

function wrapCodeSelection(before: string, after: string, fallback: string) {
  const el = codeEl.value;
  if (!el) return;
  const start = el.selectionStart;
  const end = el.selectionEnd;
  const selected = props.modelValue.slice(start, end) || fallback;
  const value = props.modelValue.slice(0, start) + before + selected + after + props.modelValue.slice(end);
  commitCodeEdit(value, start + before.length, start + before.length + selected.length);
}

function prefixCodeLines(prefix: string) {
  const el = codeEl.value;
  if (!el) return;
  const start = props.modelValue.lastIndexOf("\n", Math.max(0, el.selectionStart - 1)) + 1;
  const selectedEnd = el.selectionEnd;
  const endBreak = props.modelValue.indexOf("\n", selectedEnd);
  const end = endBreak < 0 ? props.modelValue.length : endBreak;
  const selected = props.modelValue.slice(start, end);
  const replacement = selected.split("\n").map((line) => `${prefix}${line}`).join("\n");
  commitCodeEdit(props.modelValue.slice(0, start) + replacement + props.modelValue.slice(end), start, start + replacement.length);
}

function instantiateEditor(initialValue: string) {
  if (!editorEl.value) return;
  editor?.destroy();
  lastExternalValue = initialValue;

  const specs = [
    doc.spec(),
    text.spec(),
    paragraph.spec(),
    heading.spec({ levels: [1, 2, 3, 4, 5, 6] }),
    blockquote.spec(),
    listItem.spec(),
    bulletList.spec(),
    orderedList.spec(),
    bold.spec(),
    italic.spec(),
    strike.spec(),
    underline.spec(),
    code.spec(),
    codeBlock.spec(),
    hardBreak.spec(),
    horizontalRule.spec(),
    link.spec(),
  ];

  const buildPlugins = (payload: any): any => [
    createChangePlugin(),
    ...resolvePlugins(history.plugins(), payload),
    ...resolvePlugins(paragraph.plugins(), payload),
    ...resolvePlugins(heading.plugins(), payload),
    ...resolvePlugins(blockquote.plugins(), payload),
    ...resolvePlugins(listItem.plugins(), payload),
    ...resolvePlugins(bulletList.plugins(), payload),
    ...resolvePlugins(orderedList.plugins(), payload),
    ...resolvePlugins(bold.plugins(), payload),
    ...resolvePlugins(italic.plugins(), payload),
    ...resolvePlugins(strike.plugins(), payload),
    ...resolvePlugins(underline.plugins(), payload),
    ...resolvePlugins(code.plugins(), payload),
    ...resolvePlugins(codeBlock.plugins(), payload),
    ...resolvePlugins(hardBreak.plugins(), payload),
    ...resolvePlugins(horizontalRule.plugins(), payload),
    ...resolvePlugins(link.plugins(), payload),
  ];

  editor = new MarkdownRuntime(editorEl.value, {
    state: new BangleEditorState({
      specs,
      plugins: buildPlugins as any,
      // Bangle treats string initialValue as HTML. Render Markdown to sanitized
      // structural HTML so headings, lists and intentional newlines survive
      // Bangle's own schema-aware DOM parser.
      initialValue: DOMPurify.sanitize(marked.parse(initialValue) as string),
    }),
    focusOnInit: props.autofocus,
    pmViewOpts: {
      editable: () => !props.readOnly,
    },
  });
}

function currentValue(): string {
  if (editMode.value === "code") return props.modelValue;
  if (!editor) return props.modelValue;
  return docToMarkdown(editor);
}

/** Handle typing in the raw markdown (code) textarea. */
function onCodeInput(event: Event) {
  const value = (event.target as HTMLTextAreaElement).value;
  if (value === lastExternalValue) {
    return;
  }
  lastExternalValue = value;
  emit("update:modelValue", value);
  emit("change", value);
}

watch(
  () => props.modelValue,
  (value) => {
    // In code mode the textarea binds directly to modelValue.
    if (editMode.value === "code") {
      lastExternalValue = value;
      return;
    }
    if (value === currentValue()) {
      lastExternalValue = value;
      return;
    }
    instantiateEditor(value);
  },
);

watch(
  () => props.editMode,
  (value) => {
    editMode.value = value;
  },
);

watch(
  () => props.readOnly,
  () => {
    instantiateEditor(currentValue());
  },
);

onMounted(() => {
  instantiateEditor(props.modelValue);
});

onBeforeUnmount(() => {
  editor?.destroy();
  editor = null;
});
</script>

<style scoped>
.markdown-editor {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  min-height: var(--usx-editor-min-height);
  background: var(--usx-color-background);
}

.markdown-editor__toolbar {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  min-height: var(--usx-control-size-sm);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border-bottom: 0;
  background: color-mix(in srgb, var(--usx-color-surface) 58%, transparent);
  flex-shrink: 0;
  overflow-x: auto;
  white-space: nowrap;
}

.markdown-editor__host {
  flex: 1;
  width: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* ─── Raw markdown (code) editor ────────────────────────────────── */
.markdown-editor__code {
  flex: 1;
  width: 100%;
  min-height: 0;
  resize: none;
  border: none;
  outline: none;
  box-sizing: border-box;
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface);
  font-family: var(--usx-font-family-mono);
  font-size: var(--usx-font-size-sm);
  line-height: 1.6;
  padding: clamp(var(--usx-spacing-md), 4vw, calc(var(--usx-spacing-2xl) * 1.5));
  white-space: pre-wrap;
  word-break: break-word;
  tab-size: 2;
}

.markdown-editor__code:focus {
  outline: none;
}

:deep(.ProseMirror) {
  flex: 1;
  overflow-y: auto;
  padding: clamp(var(--usx-spacing-md), 4vw, calc(var(--usx-spacing-2xl) * 1.5));
  outline: none;
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--usx-color-on-surface);
  background: var(--usx-color-surface);
  font-size: var(--usx-font-size-base);
  line-height: 1.6;
  font-family: var(--usx-font-family-sans);
}

/* Markdown formatting */
:deep(.ProseMirror strong) {
  font-weight: var(--usx-font-weight-bold);
}

:deep(.ProseMirror em) {
  font-style: italic;
}

:deep(.ProseMirror u) {
  text-decoration: underline;
}

:deep(.ProseMirror code) {
  font-family: var(--usx-font-family-mono);
  background: var(--usx-color-surface-variant);
  padding: 0 var(--usx-spacing-xs);
  border-radius: var(--usx-radius-sm);
  font-size: 0.9em;
}

:deep(.ProseMirror pre) {
  background: var(--usx-color-surface-variant);
  padding: var(--usx-spacing-md);
  border-radius: var(--usx-radius-md);
  overflow-x: auto;
  font-family: var(--usx-font-family-mono);
  line-height: 1.4;
}

:deep(.ProseMirror pre code) {
  background: transparent;
  padding: 0;
  border-radius: 0;
}

:deep(.ProseMirror blockquote) {
  padding-left: var(--usx-spacing-md);
  margin-left: 0;
  border-left: 3px solid var(--usx-color-border);
  color: var(--usx-color-on-surface-muted);
  font-style: italic;
}

:deep(.ProseMirror h1),
:deep(.ProseMirror h2),
:deep(.ProseMirror h3),
:deep(.ProseMirror h4),
:deep(.ProseMirror h5),
:deep(.ProseMirror h6) {
  margin-top: var(--usx-spacing-lg);
  margin-bottom: var(--usx-spacing-sm);
  font-weight: var(--usx-font-weight-bold);
  line-height: 1.3;
}

:deep(.ProseMirror h1) {
  font-size: var(--usx-font-size-2xl);
}

:deep(.ProseMirror h2) {
  font-size: var(--usx-font-size-xl);
}

:deep(.ProseMirror h3) {
  font-size: var(--usx-font-size-lg);
}

:deep(.ProseMirror ul),
:deep(.ProseMirror ol) {
  margin-left: var(--usx-spacing-lg);
  margin-top: var(--usx-spacing-sm);
  margin-bottom: var(--usx-spacing-sm);
}

:deep(.ProseMirror li) {
  margin-bottom: var(--usx-spacing-xs);
}

:deep(.ProseMirror p) {
  margin-bottom: var(--usx-spacing-sm);
}

.markdown-editor__host--readonly :deep(.ProseMirror) {
  background: var(--usx-color-surface-variant);
  color: var(--usx-color-on-surface-muted);
}
</style>

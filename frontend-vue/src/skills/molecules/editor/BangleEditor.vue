<template>
  <div class="bangle-editor">
    <!-- Formatting toolbar -->
    <div v-if="!readOnly" class="bangle-editor__toolbar">
      <button class="bangle-btn" title="Bold (Ctrl+B)" @click="applyBold">
        <strong>B</strong>
      </button>
      <button class="bangle-btn" title="Italic (Ctrl+I)" @click="applyItalic">
        <em>I</em>
      </button>
      <button
        class="bangle-btn"
        title="Underline (Ctrl+U)"
        @click="applyUnderline"
      >
        <u>U</u>
      </button>
      <button class="bangle-btn" title="Code" @click="applyCode">
        <code>&lt;/&gt;</code>
      </button>
      <div class="bangle-separator"></div>
      <button class="bangle-btn" title="Heading" @click="applyHeading">
        H1
      </button>
      <button class="bangle-btn" title="Block quote" @click="applyBlockquote">
        &quot;
      </button>
      <button class="bangle-btn" title="Bullet list" @click="applyBulletList">
        •
      </button>
      <button class="bangle-btn" title="Ordered list" @click="applyOrderedList">
        1.
      </button>
      <div class="bangle-separator"></div>
      <button class="bangle-btn" title="Undo" @click="undo">↶</button>
      <button class="bangle-btn" title="Redo" @click="redo">↷</button>
    </div>

    <!-- Bangle editor content area -->
    <div
      ref="editorEl"
      class="bangle-editor__host"
      :class="{
        'bangle-editor__host--code': editMode === 'code',
        'bangle-editor__host--readonly': readOnly,
      }"
    />
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import "@bangle.dev/core/style.css";
import {
  BangleEditor as BangleRuntime,
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
import {
  defaultMarkdownParser,
  defaultMarkdownSerializer,
} from "prosemirror-markdown";

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
}>();

const editorEl = ref<HTMLDivElement | null>(null);
const editMode = ref<"prose" | "code">(props.editMode);
let editor: BangleRuntime | null = null;
let lastExternalValue = props.modelValue;

function docToMarkdown(editor: BangleRuntime): string {
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
  if (!editor) return;
  bold.commands.toggleBold()(editor.view.state, editor.view.dispatch);
  editor.view.focus();
}

function applyItalic() {
  if (!editor) return;
  italic.commands.toggleItalic()(editor.view.state, editor.view.dispatch);
  editor.view.focus();
}

function applyUnderline() {
  if (!editor) return;
  underline.commands.toggleUnderline()(editor.view.state, editor.view.dispatch);
  editor.view.focus();
}

function applyCode() {
  if (!editor) return;
  code.commands.toggleCode()(editor.view.state, editor.view.dispatch);
  editor.view.focus();
}

function applyHeading() {
  if (!editor) return;
  heading.commands.toggleHeading(2)(editor.view.state, editor.view.dispatch);
  editor.view.focus();
}

function applyBlockquote() {
  if (!editor) return;
  blockquote.commands.wrapInBlockquote()(
    editor.view.state,
    editor.view.dispatch,
  );
  editor.view.focus();
}

function applyBulletList() {
  if (!editor) return;
  bulletList.commands.toggleBulletList()(
    editor.view.state,
    editor.view.dispatch,
  );
  editor.view.focus();
}

function applyOrderedList() {
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

  editor = new BangleRuntime(editorEl.value, {
    state: new BangleEditorState({
      specs,
      plugins: buildPlugins as any,
      initialValue,
    }),
    focusOnInit: props.autofocus,
    pmViewOpts: {
      editable: () => !props.readOnly,
    },
  });
}

function currentValue(): string {
  if (!editor) return props.modelValue;
  return docToMarkdown(editor);
}

watch(
  () => props.modelValue,
  (value) => {
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
.bangle-editor {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  min-height: var(--usx-editor-min-height);
  background: var(--usx-color-background);
}

.bangle-editor__toolbar {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-sm);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
  background: var(--usx-color-surface);
  flex-shrink: 0;
  overflow-x: auto;
  white-space: nowrap;
}

.bangle-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 2rem;
  height: 2rem;
  padding: 0 var(--usx-spacing-xs);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface);
  cursor: pointer;
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-medium);
  transition:
    background var(--usx-transition-fast),
    color var(--usx-transition-fast),
    border-color var(--usx-transition-fast);
}

.bangle-btn:hover {
  background: var(--usx-color-surface-hover);
  border-color: var(--usx-color-primary);
}

.bangle-btn:active {
  background: var(--usx-color-primary);
  color: var(--usx-color-on-primary);
  border-color: var(--usx-color-primary);
}

.bangle-separator {
  width: 1px;
  height: 1.5rem;
  background: var(--usx-color-border);
  margin: 0 var(--usx-spacing-xs);
}

.bangle-editor__host {
  flex: 1;
  width: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

:deep(.ProseMirror) {
  flex: 1;
  overflow-y: auto;
  padding: var(--usx-spacing-md);
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

.bangle-editor__host--readonly :deep(.ProseMirror) {
  background: var(--usx-color-surface-variant);
  color: var(--usx-color-on-surface-muted);
}
</style>

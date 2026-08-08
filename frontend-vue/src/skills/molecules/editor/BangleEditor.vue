<template>
  <div class="bangle-editor">
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

function createChangePlugin() {
  return new Plugin({
    view: () => ({
      update(view, prevState) {
        if (view.state.doc.eq(prevState.doc)) {
          return;
        }
        const value = view.state.doc.toString();
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

function instantiateEditor(initialValue: string) {
  if (!editorEl.value) return;
  editor?.destroy();
  lastExternalValue = initialValue;

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
      specs: [
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
      ],
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
  return editor?.view.state.doc.toString() ?? props.modelValue;
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
  width: 100%;
  height: 100%;
  min-height: var(--usx-editor-min-height);
}

.bangle-editor__host {
  width: 100%;
  height: 100%;
  min-height: var(--usx-editor-min-height);
}

:deep(.ProseMirror) {
  min-height: var(--usx-editor-min-height);
  padding: var(--usx-spacing-md);
  outline: none;
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--usx-color-on-surface);
  background: var(--usx-color-surface);
  font-size: var(--usx-font-size-sm);
}

:deep(.ProseMirror p),
:deep(.ProseMirror h1),
:deep(.ProseMirror h2),
:deep(.ProseMirror h3),
:deep(.ProseMirror h4),
:deep(.ProseMirror h5),
:deep(.ProseMirror h6),
:deep(.ProseMirror blockquote),
:deep(.ProseMirror ul),
:deep(.ProseMirror ol) {
  margin-top: 0;
  margin-bottom: var(--usx-spacing-sm);
}

:deep(.ProseMirror blockquote) {
  padding-left: var(--usx-spacing-md);
  border-left: var(--usx-border-width-thick) solid var(--usx-color-border);
  color: var(--usx-color-on-surface-muted);
}

.bangle-editor__host--code :deep(.ProseMirror) {
  font-family: var(--usx-font-family-mono);
}

.bangle-editor__host--readonly :deep(.ProseMirror) {
  opacity: 0.95;
}
</style>

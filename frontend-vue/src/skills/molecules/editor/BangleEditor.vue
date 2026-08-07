<template>
  <div class="bangle-editor">
    <textarea
      ref="editorEl"
      v-model="content"
      class="bangle-editor__textarea"
      :class="{
        'bangle-editor__textarea--prose': editMode === 'prose',
        'bangle-editor__textarea--code': editMode === 'code',
      }"
      :readonly="readOnly"
      spellcheck="false"
      @input="handleInput"
      @keydown="handleKeydown"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch, withDefaults } from "vue";

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

const content = ref(props.modelValue);
const editorEl = ref<HTMLTextAreaElement | null>(null);
const editMode = ref<"prose" | "code">(props.editMode);

watch(
  () => props.modelValue,
  (val) => {
    content.value = val;
  },
);

watch(
  () => props.editMode,
  (val) => {
    editMode.value = val;
  },
);

function handleInput() {
  emit("update:modelValue", content.value);
  emit("change", content.value);
}

function handleKeydown(event: KeyboardEvent) {
  const isSaveShortcut =
    (event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "s";
  if (!isSaveShortcut) {
    return;
  }

  event.preventDefault();
  emit("save", content.value);
}

onMounted(() => {
  if (props.autofocus && editorEl.value) {
    editorEl.value.focus();
  }
});
</script>

<style scoped>
.bangle-editor {
  width: 100%;
  height: 100%;
  min-height: var(--usx-editor-min-height);
}

.bangle-editor__textarea {
  width: 100%;
  height: 100%;
  border: none;
  outline: none;
  resize: none;
  padding: var(--usx-spacing-md);
  color: var(--usx-color-on-surface);
  background: var(--usx-color-surface);
  font-size: var(--usx-font-size-sm);
}

.bangle-editor__textarea--prose {
  font-family: var(--usx-font-family-sans);
  line-height: var(--usx-line-height-relaxed, 1.7);
}

.bangle-editor__textarea--code {
  font-family: var(--usx-font-family-mono);
  line-height: var(--usx-line-height-normal, 1.6);
}

.bangle-editor__textarea::placeholder {
  color: var(--usx-color-on-surface-muted);
}
</style>

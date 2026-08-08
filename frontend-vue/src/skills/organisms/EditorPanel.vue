<template>
  <div class="editor-panel">
    <!-- Bangle-first toolbar — title, engine chip, essential controls -->
    <div class="editor-panel__toolbar">
      <div class="editor-panel__toolbar-left">
        <UIcon name="article" />
        <span class="editor-panel__title">{{ title || "Untitled" }}</span>
      </div>
      <div class="editor-panel__toolbar-center">
        <span class="editor-panel__engine-chip">Bangle WYSIWYG</span>
      </div>
      <div class="editor-panel__toolbar-right">
        <button
          v-if="!readOnly"
          class="editor-panel__nav-btn editor-panel__nav-btn--save"
          @click="handleSave"
          title="Save (Ctrl+S)"
        >
          <UIcon name="save" />
        </button>
        <button
          class="editor-panel__nav-btn"
          :class="{
            'editor-panel__nav-btn--active': localEditMode === 'prose',
          }"
          :title="
            localEditMode === 'prose'
              ? 'Switch to code view'
              : 'Switch to prose view'
          "
          @click="toggleEditMode"
        >
          <UIcon :name="localEditMode === 'prose' ? 'notes' : 'code'" />
        </button>
        <button
          class="editor-panel__nav-btn"
          title="Close editor"
          @click="emit('close')"
        >
          <UIcon name="close" />
        </button>
      </div>
    </div>

    <!-- Full-width Bangle editor — WYSIWYG as primary interaction -->
    <div class="editor-panel__content">
      <BangleEditor
        v-model="localContent"
        :preview="false"
        :read-only="readOnly"
        :edit-mode="localEditMode"
        @save="handleSave"
        @change="onContentChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @component EditorPanel
 * @description Simplified markdown editor using Bangle WYSIWYG as the primary interface.
 *   - Full-width Bangle editor with unified toolbar
 *   - Essential controls: save, mode toggle, close
 *   - No preview pane (WYSIWYG eliminates need for side-by-side preview)
 * @category skills/organisms
 * @props {string} content - Markdown content (v-model)
 * @props {string} title - Display title
 * @props {boolean} readOnly - Disable edits
 * @props {'prose' | 'code'} editMode - Edit mode preference
 * @emits {string} update:content - v-model update
 * @emits {void} save - Save requested
 * @emits {void} close - Close entire editor
 */
import { ref, watch } from "vue";
import UIcon from "../atoms/UIcon.vue";
import BangleEditor from "../molecules/editor/BangleEditor.vue";

// ─── Props ───────────────────────────────────────────────────────────
interface Props {
  content?: string;
  title?: string;
  readOnly?: boolean;
  editMode?: "prose" | "code";
}

const props = withDefaults(defineProps<Props>(), {
  content: "",
  title: "Untitled",
  readOnly: false,
  editMode: "prose",
});

const emit = defineEmits<{
  "update:content": [value: string];
  "update:editMode": [value: "prose" | "code"];
  save: [value: string];
  close: [];
}>();

// ─── State ───────────────────────────────────────────────────────────
const localContent = ref(props.content);
const localEditMode = ref<"prose" | "code">(props.editMode);

// ─── Sync props ──────────────────────────────────────────────────────
watch(
  () => props.content,
  (val) => {
    localContent.value = val;
  },
);

watch(
  () => props.editMode,
  (val) => {
    localEditMode.value = val;
  },
);

// ─── Handlers ────────────────────────────────────────────────────────
function onContentChange(value: string) {
  localContent.value = value;
  emit("update:content", value);
}

function handleSave() {
  emit("save", localContent.value);
}

function toggleEditMode() {
  const next = localEditMode.value === "prose" ? "code" : "prose";
  localEditMode.value = next;
  emit("update:editMode", next);
}
</script>

<style scoped>
.editor-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  overflow: hidden;
  background: var(--usx-color-background);
}

/* ─── Toolbar — compact, essential controls only ─────────────────── */
.editor-panel__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--usx-spacing-md);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
  flex-shrink: 0;
  min-height: var(--usx-touch-min-sm);
  gap: var(--usx-spacing-sm);
}

.editor-panel__toolbar-left {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  min-width: 0;
  font-size: 1.25em;
}

.editor-panel__title {
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.editor-panel__toolbar-center {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-md);
  flex: 1;
  justify-content: center;
}

.editor-panel__engine-chip {
  display: inline-flex;
  align-items: center;
  padding: var(--usx-spacing-2) var(--usx-spacing-sm);
  border-radius: var(--usx-radius-full);
  border: var(--usx-border-width) solid var(--usx-color-border);
  background: var(--usx-color-surface-variant);
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-medium);
}

.editor-panel__toolbar-right {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-2);
  flex-shrink: 0;
}

/* ─── Nav buttons — icon-only, transparent, hover highlights ───────── */
.editor-panel__nav-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--usx-control-size-sm);
  height: var(--usx-control-size-sm);
  padding: 0;
  border: none;
  border-radius: var(--usx-radius-sm);
  background: transparent;
  color: var(--usx-color-on-surface-muted);
  cursor: pointer;
  font-size: 1.25em;
  transition:
    color var(--usx-transition-fast),
    background var(--usx-transition-fast);
}

.editor-panel__nav-btn:hover {
  background: var(--usx-color-surface-hover);
  color: var(--usx-color-on-surface);
}

.editor-panel__nav-btn--active {
  color: var(--usx-color-primary);
  background: var(--usx-color-primary-disabled);
}

.editor-panel__nav-btn--save {
  color: var(--usx-color-primary);
}

.editor-panel__nav-btn--save:hover {
  background: var(--usx-color-primary);
  color: var(--usx-color-on-primary);
}

/* ─── Full-width editor content ──────────────────────────────────── */
.editor-panel__content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}
</style>

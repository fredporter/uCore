<template>
  <div class="editor-toolbar">
    <button
      class="editor-toolbar__btn"
      :class="{ 'editor-toolbar__btn--active': sidebarOpen }"
      title="Toggle Files sidebar"
      @click="emit('toggle-sidebar')"
    >
      <UIcon name="account_tree" />
    </button>

    <!-- Edit / Preview / Split mode tabs (icon-only) -->
    <div class="editor-toolbar__mode-tabs">
      <button
        class="editor-toolbar__btn"
        :class="{ 'editor-toolbar__btn--active': viewMode === 'edit' }"
        title="Edit"
        @click="emit('update:viewMode', 'edit')"
      >
        <UIcon name="edit" />
      </button>
      <button
        class="editor-toolbar__btn"
        :class="{ 'editor-toolbar__btn--active': viewMode === 'preview' }"
        title="Preview"
        @click="emit('update:viewMode', 'preview')"
      >
        <UIcon name="visibility" />
      </button>
      <button
        class="editor-toolbar__btn"
        :class="{ 'editor-toolbar__btn--active': viewMode === 'split' }"
        title="Split (editor + preview)"
        @click="emit('update:viewMode', 'split')"
      >
        <UIcon name="vertical_split" />
      </button>
    </div>

    <button
      v-if="!readOnly"
      class="editor-toolbar__btn editor-toolbar__btn--save"
      title="Save (Ctrl+S)"
      @click="emit('save')"
    >
      <UIcon name="save" />
    </button>

    <button
      class="editor-toolbar__btn"
      :class="{ 'editor-toolbar__btn--active': researchOpen }"
      title="Research panel"
      @click="emit('toggle-research')"
    >
      <UIcon name="science" />
    </button>

    <button
      class="editor-toolbar__btn"
      :class="{ 'editor-toolbar__btn--active': editMode === 'code' }"
      :title="
        editMode === 'prose' ? 'Switch to code view' : 'Switch to prose view'
      "
      @click="emit('toggle-edit-mode')"
    >
      <UIcon :name="editMode === 'prose' ? 'notes' : 'code'" />
    </button>

    <button
      class="editor-toolbar__btn"
      title="Close editor"
      @click="emit('close')"
    >
      <UIcon name="close" />
    </button>
  </div>
</template>

<script setup lang="ts">
/**
 * @component EditorToolbar
 * @description Compact, icon-only control row for the editor panel: sidebar
 * toggle, Edit/Preview/Split view modes, save, research, prose/code edit mode,
 * and close. Rendered inside the MarkdownEditor toolbar (or a slim preview
 * bar when in Preview-only mode) so the editor keeps a single toolbar.
 * @category skills/molecules
 * @props {string} viewMode - 'edit' | 'preview' | 'split'
 * @props {boolean} researchOpen - Research panel visibility
 * @props {string} editMode - 'prose' | 'code'
 * @props {boolean} readOnly - Hide save when read-only
 * @props {boolean} sidebarOpen - Files sidebar visibility (active highlight)
 * @emits update:viewMode, toggle-sidebar, toggle-research, toggle-edit-mode, save, close
 */
import UIcon from "../../atoms/UIcon.vue";

interface Props {
  viewMode: "edit" | "preview" | "split";
  researchOpen: boolean;
  editMode: "prose" | "code";
  readOnly?: boolean;
  sidebarOpen?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  readOnly: false,
  sidebarOpen: false,
});

const emit = defineEmits<{
  "update:viewMode": [value: "edit" | "preview" | "split"];
  "toggle-sidebar": [];
  "toggle-research": [];
  "toggle-edit-mode": [];
  save: [];
  close: [];
}>();
</script>

<style scoped>
.editor-toolbar {
  display: inline-flex;
  align-items: center;
  gap: var(--usx-spacing-2);
  margin-left: var(--usx-spacing-sm);
  padding-left: var(--usx-spacing-sm);
  border-left: 1px solid var(--usx-color-border);
  flex-shrink: 0;
}

.editor-toolbar__btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 2rem;
  min-height: 0;
  height: 2rem;
  padding: 0 var(--usx-spacing-xs);
  border: none;
  border-radius: var(--usx-radius-sm);
  background: transparent;
  color: var(--usx-color-on-surface-muted);
  cursor: pointer;
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-medium);
  transition:
    background var(--usx-transition-fast),
    color var(--usx-transition-fast);
}

.editor-toolbar__btn .u-icon,
.editor-toolbar__btn .material-symbols-outlined {
  font-size: 18px;
  line-height: 1;
  font-variation-settings:
    "FILL" 0,
    "wght" 400,
    "GRAD" 0,
    "opsz" 20;
}

.editor-toolbar__btn:hover {
  background: var(--usx-color-surface-hover);
  color: var(--usx-color-on-surface);
}

.editor-toolbar__btn--active {
  background: var(--usx-color-surface);
  color: var(--usx-color-primary);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.editor-toolbar__btn--save {
  color: var(--usx-color-primary);
}

.editor-toolbar__btn--save:hover {
  color: var(--usx-color-on-surface);
}

/* Mode tabs: subtle segmented grouping */
.editor-toolbar__mode-tabs {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  background-color: var(--usx-color-background);
  border: 1px solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  padding: 2px;
}
</style>

<template>
  <div
    class="editor-toolbar"
    :class="{
      'editor-toolbar--bare': bare,
      'editor-toolbar--right': right,
    }"
  >
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
 * @description Compact, icon-only view-research-close control row for the
 * editor panel: Edit/Preview/Split view modes, save, research, prose/code edit
 * mode, and close. Rendered on the Prose panel, or right-aligned inside the
 * editor toolbar in editor-only view. The Files sidebar toggle lives in the
 * global toolbar, not here.
 * @category skills/molecules
 * @props {string} viewMode - 'edit' | 'preview' | 'split'
 * @props {boolean} researchOpen - Research panel visibility
 * @props {string} editMode - 'prose' | 'code'
 * @props {boolean} readOnly - Hide save when read-only
 * @props {boolean} bare - Drop left margin/separator (sits alone in a bar)
 * @props {boolean} right - Push to the right edge of the parent toolbar
 * @emits update:viewMode, toggle-research, toggle-edit-mode, save, close
 */
import UIcon from "../../atoms/UIcon.vue";

interface Props {
  viewMode: "edit" | "preview" | "split";
  researchOpen: boolean;
  editMode: "prose" | "code";
  readOnly?: boolean;
  bare?: boolean;
  right?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  readOnly: false,
  bare: false,
  right: false,
});

const emit = defineEmits<{
  "update:viewMode": [value: "edit" | "preview" | "split"];
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

/* Sits alone in a bar (no preceding controls) — drop the left separator */
.editor-toolbar--bare {
  margin-left: 0;
  padding-left: 0;
  border-left: none;
}

/* Right-aligned inside the editor toolbar (editor-only view) */
.editor-toolbar--right {
  margin-left: auto;
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

/* Mode tabs: subtle segmented grouping. Uses an inset ring (no real border or
   padding) so the wrapper adds ZERO height — the toolbar stays 2rem tall and
   matches the editor toolbar height when side by side. */
.editor-toolbar__mode-tabs {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 0;
  border: none;
  background: transparent;
  border-radius: var(--usx-radius-md);
  box-shadow: inset 0 0 0 1px var(--usx-color-border);
}
</style>

/**
 * @component EditorToolbar
 * @description File tab bar + action buttons for the unified code editor.
 * Matches the uCore .wf-toolbar pattern.
 */
<template>
  <div class="editor-toolbar">
    <div class="editor-toolbar__tabs">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        class="editor-toolbar__tab"
        :class="{ 'editor-toolbar__tab--active': tab.id === activeTabId, 'editor-toolbar__tab--dirty': tab.dirty }"
        :title="tab.path"
        @click="$emit('select-tab', tab.id)"
      >
        <UIcon :name="tabIcon(tab.filename)" class="editor-toolbar__tab-icon" />
        <span class="editor-toolbar__tab-name">{{ tab.filename }}</span>
        <span v-if="tab.dirty" class="editor-toolbar__tab-dot" />
        <button class="editor-toolbar__tab-close" @click.stop="$emit('close-tab', tab.id)">
          <UIcon name="close" :size="12" />
        </button>
      </button>
      <button v-if="showAddTab" class="editor-toolbar__add" @click="$emit('add-tab')">
        <UIcon name="add" />
      </button>
    </div>

    <div class="editor-toolbar__actions">
      <button v-if="showDiff" class="editor-toolbar__btn"
        title="Diff"
        :class="{ 'editor-toolbar__btn--active': diffActive }" @click="$emit('toggle-diff')">
        <UIcon name="difference" :size="18" />
      </button>
      <button v-if="showCells" class="editor-toolbar__btn"
        title="Cells"
        :class="{ 'editor-toolbar__btn--active': cellsActive }" @click="$emit('toggle-cells')">
        <UIcon name="vertical_split" :size="18" />
      </button>
      <button v-if="showPreview" class="editor-toolbar__btn"
        title="Preview"
        :class="{ 'editor-toolbar__btn--active': previewActive }" @click="$emit('toggle-preview')">
        <UIcon name="visibility" :size="18" />
      </button>
      <button v-if="showCloseSecondary" class="editor-toolbar__btn" @click="$emit('close-secondary')">
        <UIcon name="close_fullscreen" />
      </button>
      <button
        class="editor-toolbar__btn editor-toolbar__btn--save"
        title="Save"
        aria-label="Save"
        :disabled="!dirty || readOnly"
        @click="$emit('save')"
      >
        <UIcon name="save" :size="18" />
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import UIcon from "../../atoms/UIcon.vue";

export interface EditorTab {
  id: string;
  filename: string;
  path: string;
  dirty: boolean;
  language?: string;
}

interface Props {
  tabs?: EditorTab[];
  activeTabId?: string;
  dirty?: boolean;
  readOnly?: boolean;
  diffActive?: boolean;
  cellsActive?: boolean;
  previewActive?: boolean;
  showDiff?: boolean;
  showCells?: boolean;
  showPreview?: boolean;
  showCloseSecondary?: boolean;
  showAddTab?: boolean;
}

withDefaults(defineProps<Props>(), {
  tabs: () => [],
  activeTabId: "",
  dirty: false,
  readOnly: false,
  diffActive: false,
  cellsActive: false,
  previewActive: false,
  showDiff: true,
  showCells: true,
  showPreview: false,
  showCloseSecondary: false,
  showAddTab: false,
});

defineEmits<{
  "select-tab": [id: string];
  "close-tab": [id: string];
  "add-tab": [];
  "toggle-diff": [];
  "toggle-cells": [];
  "toggle-preview": [];
  "close-secondary": [];
  save: [];
}>();

function tabIcon(filename: string): string {
  const ext = filename.split(".").pop()?.toLowerCase();
  const map: Record<string, string> = {
    ts:"code", tsx:"code", js:"code", jsx:"code", py:"code",
    html:"html", css:"css", scss:"palette", json:"data_object",
    yaml:"list", yml:"list", md:"article", mdx:"article",
  };
  return map[ext ?? ""] || "description";
}
</script>

<style scoped>
.editor-toolbar {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: 0 var(--usx-spacing-xs);
  min-height: var(--usx-control-size-sm);
  flex-shrink: 0;
  background: var(--usx-color-surface);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
  overflow: hidden;
}
.editor-toolbar__tabs {
  display: flex;
  align-items: stretch;
  flex: 1;
  min-width: 0;
  overflow-x: auto;
  gap: 0;
  padding: var(--usx-spacing-xs) 0;
}
.editor-toolbar__tab {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border: var(--usx-border-width) solid transparent;
  background: transparent;
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
  cursor: pointer;
  white-space: nowrap;
  min-height: 0;
  border-radius: var(--usx-radius-sm) var(--usx-radius-sm) 0 0;
  transition: background var(--usx-transition-fast), color var(--usx-transition-fast);
}
.editor-toolbar__tab:hover {
  background: var(--usx-color-surface-variant);
  color: var(--usx-color-on-surface);
}
.editor-toolbar__tab--active {
  background: var(--usx-color-background);
  color: var(--usx-color-on-surface);
  border-color: var(--usx-color-border);
  border-bottom-color: transparent;
}
.editor-toolbar__tab--dirty .editor-toolbar__tab-name {
  font-style: italic;
}
.editor-toolbar__tab-icon {
  flex-shrink: 0;
}
.editor-toolbar__tab-name {
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
}
.editor-toolbar__tab-dot {
  width: var(--usx-spacing-xs);
  height: var(--usx-spacing-xs);
  border-radius: 50%;
  background: var(--usx-color-warning);
  flex-shrink: 0;
}
.editor-toolbar__tab-close {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--usx-spacing-xs);
  border: none;
  background: transparent;
  color: var(--usx-color-on-surface-muted);
  cursor: pointer;
  border-radius: var(--usx-radius-sm);
  min-height: 0;
  opacity: 0;
  transition: opacity var(--usx-transition-fast);
}
.editor-toolbar__tab:hover .editor-toolbar__tab-close,
.editor-toolbar__tab--active .editor-toolbar__tab-close {
  opacity: 1;
}
.editor-toolbar__tab-close:hover {
  color: var(--usx-color-danger);
  background: color-mix(in srgb, var(--usx-color-danger) 15%, transparent);
}
.editor-toolbar__add {
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--usx-control-size-sm);
  height: var(--usx-control-size-sm);
  border: none;
  background: transparent;
  color: var(--usx-color-on-surface-muted);
  cursor: pointer;
  border-radius: var(--usx-radius-sm);
  flex-shrink: 0;
  min-height: 0;
}
.editor-toolbar__add:hover {
  color: var(--usx-color-primary);
  background: var(--usx-color-surface-variant);
}
.editor-toolbar__actions {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  flex-shrink: 0;
}
.editor-toolbar__btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: var(--usx-control-size-sm);
  height: var(--usx-control-size-sm);
  padding: 0;
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-xs);
  cursor: pointer;
  min-height: 0;
  transition: border-color var(--usx-transition-fast), color var(--usx-transition-fast);
}
.editor-toolbar__btn:disabled {
  opacity: 0.4;
  cursor: default;
}
.editor-toolbar__btn--save:not(:disabled) {
  border-color: var(--usx-color-primary);
  color: var(--usx-color-primary);
}
.editor-toolbar__btn:hover {
  border-color: var(--usx-color-primary); color: var(--usx-color-on-surface);
}
.editor-toolbar__btn--active {
  border-color: var(--usx-color-primary); color: var(--usx-color-primary);
  background: color-mix(in srgb, var(--usx-color-primary) 8%, transparent);
}
</style>

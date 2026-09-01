/**
 * @component EditorStatusBar
 * @description Bottom status bar showing language, cursor position, encoding, dirty state.
 */
<template>
  <div class="editor-status-bar">
    <span class="editor-status-bar__item">{{ languageLabel }}</span>
    <span class="editor-status-bar__item">Ln {{ cursor.line }}, Col {{ cursor.col }}</span>
    <span class="editor-status-bar__item">UTF-8</span>
    <span class="editor-status-bar__item">
      <span v-if="lineCount > 0">{{ lineCount }} lines</span>
    </span>
    <span v-if="dirty" class="editor-status-bar__item editor-status-bar__item--dirty">Unsaved</span>
    <span v-if="readOnly" class="editor-status-bar__item editor-status-bar__item--readonly">Read-only</span>
    <span class="editor-status-bar__spacer" />
    <slot name="extra" />
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { languageLabel } from "./codeLanguages";

interface Props {
  language?: string;
  cursor?: { line: number; col: number };
  lineCount?: number;
  dirty?: boolean;
  readOnly?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  language: "markdown",
  cursor: () => ({ line: 1, col: 1 }),
  lineCount: 0,
  dirty: false,
  readOnly: false,
});
</script>

<style scoped>
.editor-status-bar {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  min-height: var(--usx-control-size-sm);
  flex-shrink: 0;
  background: var(--usx-color-surface-variant);
  border-top: var(--usx-border-width) solid var(--usx-color-border);
  font-size: var(--usx-font-size-xs);
  font-family: var(--usx-font-family-mono);
  color: var(--usx-color-on-surface-muted);
  overflow: hidden;
  user-select: none;
}

.editor-status-bar__item {
  white-space: nowrap;
  flex-shrink: 0;
}

.editor-status-bar__item--dirty {
  color: var(--usx-color-warning);
}

.editor-status-bar__item--readonly {
  color: var(--usx-color-danger);
}

.editor-status-bar__spacer {
  flex: 1;
  min-width: 0;
}
</style>

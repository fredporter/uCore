<template>
  <div class="markdown-preview">
    <div
      :id="props.previewId"
      class="markdown-preview__content"
      v-html="html"
    ></div>
  </div>
</template>

<script setup lang="ts">
/**
 * @component MarkdownPreview
 * @description Read-only markdown renderer Skill.
 * Used for displaying rendered markdown content without editing capabilities.
 * @category skills/molecules
 * @props {string} content - Markdown content to render
 * @props {string} previewId - Unique ID for the preview container
 * @usage
 *   <MarkdownPreview :content="doc.content" preview-id="doc-viewer" />
 */
import { computed, withDefaults } from "vue";
import { renderMarkdown } from "../../../composables/useMarkdown";

interface Props {
  content?: string;
  previewId?: string;
}

const props = withDefaults(defineProps<Props>(), {
  content: "",
  previewId: "markdown-preview",
});

const html = computed(() => renderMarkdown(props.content ?? ""));
</script>

<style scoped>
.markdown-preview {
  width: 100%;
  flex: 1;
  overflow-y: auto;
  background: var(--usx-color-surface);
}

.markdown-preview__content {
  line-height: 1.7;
  padding: var(--usx-spacing-md);
  min-height: 100%;
}
</style>

<template>
  <BangleEditor
    :model-value="props.modelValue"
    :toolbars="props.toolbars"
    :preview="props.preview"
    :html-preview="props.htmlPreview"
    :no-upload="props.noUpload"
    :autofocus="props.autofocus"
    @update:model-value="(value) => emit('update:modelValue', value)"
    @change="(value) => emit('change', value)"
    @save="(value) => emit('save', value)"
  />
</template>

<script setup lang="ts">
/**
 * @component MarkdownEditor
 * @description Backward-compatible markdown editor wrapper now backed by BangleEditor.
 * @category skills/molecules
 * @props {string} modelValue - v-model markdown content
 * @props {string[]} toolbars - Custom toolbar configuration
 * @props {boolean} preview - Show live preview
 * @props {boolean} htmlPreview - Enable HTML preview
 * @props {boolean} noUpload - Disable image upload
 * @props {boolean} autofocus - Auto-focus on mount
 * @emits {string} update:modelValue - v-model update
 * @emits {string} save - Ctrl+S save event
 * @emits {string} change - Content changed
 */
import { withDefaults } from "vue";
import BangleEditor from "./BangleEditor.vue";

interface Props {
  modelValue?: string;
  toolbars?: string[];
  preview?: boolean;
  htmlPreview?: boolean;
  noUpload?: boolean;
  autofocus?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: "",
  toolbars: undefined,
  preview: true,
  htmlPreview: false,
  noUpload: false,
  autofocus: false,
});

const emit = defineEmits<{
  "update:modelValue": [value: string];
  save: [value: string];
  change: [value: string];
}>();
</script>

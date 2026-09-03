<template>
  <button
    type="button"
    class="toolbar-button"
    :class="{ 'toolbar-button--active': active }"
    :title="shortcut ? `${label} (${shortcut})` : label"
    :aria-label="shortcut ? `${label}, ${shortcut}` : label"
    :aria-pressed="toggle ? active : undefined"
    :disabled="disabled"
    @click="$emit('activate')"
  >
    <UIcon :name="icon" />
  </button>
</template>

<script setup lang="ts">
import UIcon from "../../atoms/UIcon.vue";
withDefaults(defineProps<{
  label: string;
  icon: string;
  shortcut?: string;
  active?: boolean;
  toggle?: boolean;
  disabled?: boolean;
}>(), { shortcut: "", active: false, toggle: false, disabled: false });
defineEmits<{ activate: [] }>();
</script>

<style scoped>
.toolbar-button { display: inline-flex; align-items: center; justify-content: center; width: var(--usx-control-size-sm); height: var(--usx-control-size-sm); min-width: var(--usx-control-size-sm); min-height: var(--usx-control-size-sm); padding: 0; border: var(--usx-border-width) solid transparent; border-radius: var(--usx-radius-sm); background: transparent; color: var(--usx-color-on-surface); cursor: pointer; }
.toolbar-button:hover, .toolbar-button:focus-visible { background: var(--usx-color-surface-hover); color: var(--usx-color-primary); }
.toolbar-button--active { background: var(--usx-color-primary); color: var(--usx-color-on-primary); }
.toolbar-button:disabled { opacity: .4; cursor: default; }
</style>

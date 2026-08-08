<template>
  <div class="binder-mission-filter">
    <label class="binder-mission-filter__label">Binder / Mission</label>
    <select
      v-model="selectedBinder"
      class="binder-mission-filter__select"
      @change="onChange"
    >
      <option value="">All Binders</option>
      <option v-for="binder in binders" :key="binder.id" :value="binder.id">
        {{ binder.name }}
      </option>
    </select>
  </div>
</template>

<script setup lang="ts">
/**
 * @component BinderMissionFilter
 * @description Binder/Mission selector filter for the filepicker.
 * Dynamically populated from search results.
 * @category molecules
 * @emits {string} binder-change - Selected binder ID
 * @usage <BinderMissionFilter @binder-change="onBinderChange" />
 */
import { ref } from "vue";

interface Binder {
  id: string;
  name: string;
}

const selectedBinder = ref("Sandbox");
const binders = ref<Binder[]>([
  { id: "Sandbox", name: "Sandbox" },
  { id: "active", name: "Active" },
  { id: "docs", name: "Documentation" },
  { id: "archive", name: "Archive" },
]);

const emit = defineEmits<{
  "binder-change": [binder: string];
}>();

function onChange() {
  emit("binder-change", selectedBinder.value);
}

// Allow external population of binders from search results
function setBinders(newBinders: Binder[]) {
  binders.value = newBinders;
}

defineExpose({ setBinders });
</script>

<style scoped>
.binder-mission-filter {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
}

.binder-mission-filter__label {
  margin: 0;
  font-size: var(--filepicker-filter-label-size, var(--usx-font-size-sm));
  font-weight: var(
    --filepicker-filter-label-weight,
    var(--usx-font-weight-semibold)
  );
  text-transform: var(--filepicker-filter-label-transform, none);
  color: var(--filepicker-filter-label-color, var(--usx-color-on-surface));
  letter-spacing: var(--filepicker-filter-label-spacing, 0.01em);
}

.binder-mission-filter__select {
  width: 100%;
  display: block;
  margin: 0;
  min-height: var(--filepicker-select-min-height, var(--usx-touch-min));
  height: var(--filepicker-select-height, var(--usx-touch-min));
  line-height: 1.2;
  padding: var(--filepicker-select-padding-y, var(--usx-spacing-sm))
    calc(
      var(--filepicker-select-padding-x, var(--usx-spacing-md)) +
        var(--usx-spacing-lg)
    )
    var(--filepicker-select-padding-y, var(--usx-spacing-sm))
    var(--filepicker-select-padding-x, var(--usx-spacing-md));
  background: var(--filepicker-select-bg, var(--usx-color-background));
  background-image:
    linear-gradient(45deg, transparent 50%, currentColor 50%),
    linear-gradient(135deg, currentColor 50%, transparent 50%);
  background-position:
    calc(100% - var(--usx-spacing-md)) calc(50% - 2px),
    calc(100% - var(--usx-spacing-sm)) calc(50% - 2px);
  background-size:
    6px 6px,
    6px 6px;
  background-repeat: no-repeat;
  border-radius: var(--filepicker-select-radius, var(--usx-radius-sm));
  font-size: var(--filepicker-select-font-size, var(--usx-font-size-sm));
  font-family: var(--usx-font-family-sans);
  font-weight: var(--usx-font-weight-medium);
  color: var(--usx-color-on-surface);
  border: var(--filepicker-select-border-width, var(--usx-border-width-thick))
    solid
    var(
      --filepicker-select-border-color,
      color-mix(in srgb, var(--usx-color-primary) 15%, transparent)
    );
  cursor: pointer;
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;
  box-sizing: border-box;
}

.binder-mission-filter__select:focus {
  border-color: var(--usx-color-primary);
  outline: none;
}
</style>

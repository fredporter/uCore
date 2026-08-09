<template>
  <div v-if="rows.length > 0" class="frontmatter-pills">
    <div class="frontmatter-pills__grid">
      <div
        v-for="row in rows"
        :key="row.key"
        class="frontmatter-pills__cell"
        :class="`frontmatter-pills__cell--${row.type}`"
      >
        <span class="frontmatter-pills__cell-key">{{ row.key }}</span>
        <span class="frontmatter-pills__cell-value">
          <input
            v-if="isEditing(row)"
            ref="editInputEl"
            v-model="editValue"
            class="frontmatter-pills__input"
            @keydown.enter="confirmEdit"
            @keydown.escape="cancelEdit"
            @blur="confirmEdit"
          />
          <span v-else class="frontmatter-pills__cell-display">{{
            row.display
          }}</span>
        </span>
        <span v-if="canEdit" class="frontmatter-pills__cell-actions">
          <button
            class="frontmatter-pills__action"
            title="Edit field"
            @click="editRow(row)"
          >
            <UIcon name="edit" />
          </button>
          <button
            class="frontmatter-pills__action frontmatter-pills__action--remove"
            title="Remove field"
            @click="removeRow(row.key)"
          >
            <UIcon name="close" />
          </button>
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @component FrontmatterPills
 * @description Editable YAML frontmatter metadata, displayed as a compact
 * key/value table with inline editing and removal.
 */
import { computed, ref, nextTick } from "vue";
import UIcon from "../../atoms/UIcon.vue";
import type { Frontmatter } from "../../../utils/frontmatterParser";

interface Props {
  modelValue: Frontmatter;
  canEdit?: boolean;
}

const props = withDefaults(defineProps<Props>(), { canEdit: true });
const emit = defineEmits<{ "update:modelValue": [value: Frontmatter] }>();

interface Row {
  key: string;
  display: string;
  rawValue: string;
  type: "tag" | "status" | "date" | "author" | "source" | "generic";
}

const rows = computed<Row[]>(() => {
  return Object.entries(props.modelValue).map(([key, value]) => {
    const raw = Array.isArray(value) ? value.join(", ") : String(value ?? "");
    return {
      key,
      rawValue: raw,
      display: formatDisplay(key, value),
      type: classifyKey(key),
    };
  });
});

function classifyKey(key: string): Row["type"] {
  if (key === "tags") return "tag";
  if (key === "status") return "status";
  if (key === "date" || key === "created" || key === "updated") return "date";
  if (key === "author") return "author";
  if (key === "source") return "source";
  return "generic";
}

function formatDisplay(key: string, value: unknown): string {
  if (key === "tags") {
    const arr = Array.isArray(value) ? value : [String(value)];
    return arr.map((t) => (String(t).startsWith("#") ? t : `#${t}`)).join(" ");
  }
  if (key === "source") {
    try {
      return new URL(String(value)).hostname;
    } catch {
      return String(value);
    }
  }
  return String(value);
}

// ─── Edit (inline in the value cell) ──────────────────────────
const editTarget = ref<Row | null>(null);
const editValue = ref("");
const editInputEl = ref<HTMLInputElement | null>(null);

function isEditing(row: Row): boolean {
  return editTarget.value?.key === row.key;
}

function editRow(row: Row) {
  if (!props.canEdit) return;
  editTarget.value = row;
  editValue.value = row.rawValue;
  nextTick(() => {
    editInputEl.value?.focus();
    editInputEl.value?.select();
  });
}

function confirmEdit() {
  if (!editTarget.value) return;
  const updated = { ...props.modelValue };
  const key = editTarget.value.key;
  // Re-parse value from string
  if (editValue.value.includes(",")) {
    updated[key] = editValue.value.split(",").map((s) => s.trim());
  } else {
    updated[key] = editValue.value;
  }
  emit("update:modelValue", updated);
  editTarget.value = null;
}

function cancelEdit() {
  editTarget.value = null;
}

function removeRow(key: string) {
  const updated = { ...props.modelValue };
  delete updated[key];
  emit("update:modelValue", updated);
  editTarget.value = null;
}
</script>

<style scoped>
.frontmatter-pills {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
}

/* ─── Condensed multi-column grid (stacks in narrow views) ──────── */
.frontmatter-pills__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: var(--usx-spacing-2) var(--usx-spacing-sm);
}

.frontmatter-pills__cell {
  display: flex;
  align-items: baseline;
  gap: var(--usx-spacing-xs);
  min-width: 0;
  padding: 1px var(--usx-spacing-sm);
  border: 1px solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: var(--usx-color-surface);
  font-size: var(--usx-font-size-xs);
  font-family: var(--usx-font-family-sans);
}

.frontmatter-pills__cell-key {
  color: var(--usx-color-on-surface-muted);
  font-weight: var(--usx-font-weight-medium);
  white-space: nowrap;
  flex-shrink: 0;
}

.frontmatter-pills__cell-value {
  min-width: 0;
  flex: 1;
}

.frontmatter-pills__cell-display {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--usx-color-on-surface);
}

.frontmatter-pills__cell--tag .frontmatter-pills__cell-display {
  color: var(--usx-color-info);
}

.frontmatter-pills__cell--source .frontmatter-pills__cell-display {
  color: var(--usx-color-primary);
}

.frontmatter-pills__cell--status .frontmatter-pills__cell-display {
  color: var(--usx-color-success);
}

.frontmatter-pills__cell-actions {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  flex-shrink: 0;
  opacity: 0;
  transition: opacity var(--usx-transition-fast);
}

.frontmatter-pills__cell:hover .frontmatter-pills__cell-actions,
.frontmatter-pills__cell:focus-within .frontmatter-pills__cell-actions {
  opacity: 1;
}

.frontmatter-pills__action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  min-height: 0;
  padding: 0;
  border: none;
  border-radius: var(--usx-radius-sm);
  background: transparent;
  color: var(--usx-color-on-surface-muted);
  cursor: pointer;
  transition:
    background var(--usx-transition-fast),
    color var(--usx-transition-fast);
}

.frontmatter-pills__action:hover {
  background: var(--usx-color-surface-hover);
  color: var(--usx-color-on-surface);
}

.frontmatter-pills__action--remove:hover {
  color: var(--usx-color-danger);
}

.frontmatter-pills__input {
  width: 100%;
  padding: 1px var(--usx-spacing-xs);
  border: 1px solid var(--usx-color-primary);
  border-radius: var(--usx-radius-sm);
  background-color: var(--usx-color-background);
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-xs);
  font-family: var(--usx-font-family-mono);
  outline: none;
}
</style>

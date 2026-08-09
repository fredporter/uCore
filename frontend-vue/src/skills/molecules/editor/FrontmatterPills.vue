<template>
  <div v-if="rows.length > 0 || canEdit" class="frontmatter-pills">
    <table class="frontmatter-pills__table">
      <tbody>
        <tr
          v-for="row in rows"
          :key="row.key"
          class="frontmatter-pills__row"
          :class="`frontmatter-pills__row--${row.type}`"
        >
          <th class="frontmatter-pills__key" scope="row">{{ row.key }}</th>
          <td class="frontmatter-pills__value">
            <input
              v-if="isEditing(row)"
              ref="editInputEl"
              v-model="editValue"
              class="frontmatter-pills__input"
              @keydown.enter="confirmEdit"
              @keydown.escape="cancelEdit"
              @blur="confirmEdit"
            />
            <span v-else>{{ row.display }}</span>
          </td>
          <td v-if="canEdit" class="frontmatter-pills__actions">
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
          </td>
        </tr>
      </tbody>
    </table>

    <button
      v-if="canEdit"
      class="frontmatter-pills__add"
      title="Add field"
      @click="addRow"
    >
      <UIcon name="add" /> Add field
    </button>
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

function addRow() {
  const key = window.prompt("New field name (e.g. status, author):");
  if (!key?.trim()) return;
  const value = window.prompt(`Value for "${key}":`);
  if (value === null) return;
  emit("update:modelValue", { ...props.modelValue, [key.trim()]: value });
}
</script>

<style scoped>
.frontmatter-pills {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
}

/* ─── Table ─────────────────────────────────────────────────── */
.frontmatter-pills__table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--usx-font-size-xs);
  font-family: var(--usx-font-family-sans);
}

.frontmatter-pills__row {
  border-top: 1px solid var(--usx-color-border);
}

.frontmatter-pills__key {
  width: 30%;
  min-width: 96px;
  padding: 2px var(--usx-spacing-sm) 2px 0;
  text-align: left;
  font-weight: var(--usx-font-weight-medium);
  color: var(--usx-color-on-surface-muted);
  vertical-align: top;
  white-space: nowrap;
}

.frontmatter-pills__value {
  padding: 2px var(--usx-spacing-sm);
  color: var(--usx-color-on-surface);
  word-break: break-word;
}

.frontmatter-pills__row--tag .frontmatter-pills__value {
  color: var(--usx-color-info);
}

.frontmatter-pills__row--source .frontmatter-pills__value {
  color: var(--usx-color-primary);
}

.frontmatter-pills__row--status .frontmatter-pills__value {
  color: var(--usx-color-success);
}

.frontmatter-pills__actions {
  width: 1%;
  padding: 2px 0 2px var(--usx-spacing-xs);
  text-align: right;
  white-space: nowrap;
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

/* ─── Add field ─────────────────────────────────────────────── */
.frontmatter-pills__add {
  display: inline-flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  align-self: flex-start;
  min-height: 0;
  height: 1.75rem;
  padding: 0 var(--usx-spacing-sm);
  border: 1px dashed var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: transparent;
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-xs);
  font-family: var(--usx-font-family-sans);
  cursor: pointer;
  transition:
    color var(--usx-transition-fast),
    border-color var(--usx-transition-fast);
}

.frontmatter-pills__add:hover {
  color: var(--usx-color-primary);
  border-color: var(--usx-color-primary);
}
</style>

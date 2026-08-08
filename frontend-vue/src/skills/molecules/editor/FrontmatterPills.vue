<template>
  <div v-if="pills.length > 0 || canEdit" class="frontmatter-pills">
    <div class="frontmatter-pills__list">
      <button
        v-for="pill in pills"
        :key="pill.key"
        class="frontmatter-pill"
        :class="`frontmatter-pill--${pill.type}`"
        :title="`${pill.key}: ${pill.rawValue}`"
        @click="editPill(pill)"
      >
        <span v-if="pill.type === 'status'" class="frontmatter-pill__dot" />
        <span class="frontmatter-pill__label">{{ pill.display }}</span>
      </button>

      <button
        v-if="canEdit"
        class="frontmatter-pill frontmatter-pill--add"
        @click="addPill"
      >
        <UIcon name="add" />
      </button>
    </div>

    <!-- Inline edit popover -->
    <div v-if="editTarget" class="frontmatter-pill-edit">
      <span class="frontmatter-pill-edit__key">{{ editTarget.key }}</span>
      <input
        ref="editInputEl"
        v-model="editValue"
        class="frontmatter-pill-edit__input"
        @keydown.enter="confirmEdit"
        @keydown.escape="cancelEdit"
        @blur="cancelEdit"
      />
      <button
        class="frontmatter-pill-edit__delete"
        title="Remove"
        @mousedown.prevent="removePill(editTarget.key)"
      >
        <UIcon name="close" />
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @component FrontmatterPills
 * @description Visual editable pills for YAML frontmatter metadata.
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

interface Pill {
  key: string;
  display: string;
  rawValue: string;
  type: "tag" | "status" | "date" | "author" | "source" | "generic";
}

const STATUS_COLORS: Record<string, string> = {
  draft: "warning",
  published: "success",
  archived: "muted",
  review: "info",
};

const pills = computed<Pill[]>(() => {
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

function classifyKey(key: string): Pill["type"] {
  if (key === "tags") return "tag";
  if (key === "status") return "status";
  if (key === "date" || key === "created" || key === "updated") return "date";
  if (key === "author") return "author";
  if (key === "source") return "source";
  return "generic";
}

function formatDisplay(key: string, value: unknown): string {
  if (key === "title") return String(value).slice(0, 20);
  if (key === "tags") {
    const arr = Array.isArray(value) ? value : [String(value)];
    return arr.map((t) => (String(t).startsWith("#") ? t : `#${t}`)).join(" ");
  }
  if (key === "source") {
    try {
      return new URL(String(value)).hostname;
    } catch {
      return String(value).slice(0, 20);
    }
  }
  if (key === "date" || key === "created" || key === "updated") {
    return `${key}: ${String(value).slice(0, 10)}`;
  }
  return `${key}: ${String(value).slice(0, 16)}`;
}

// ─── Edit ────────────────────────────────────────────────────
const editTarget = ref<Pill | null>(null);
const editValue = ref("");
const editInputEl = ref<HTMLInputElement | null>(null);

async function editPill(pill: Pill) {
  if (!props.canEdit) return;
  editTarget.value = pill;
  editValue.value = pill.rawValue;
  await nextTick();
  editInputEl.value?.focus();
  editInputEl.value?.select();
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

function removePill(key: string) {
  const updated = { ...props.modelValue };
  delete updated[key];
  emit("update:modelValue", updated);
  editTarget.value = null;
}

function addPill() {
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
  padding: var(--usx-spacing-xs) var(--usx-spacing-md);
  border-bottom: 1px solid var(--usx-color-border);
  background-color: var(--usx-color-surface-variant);
}

.frontmatter-pills__list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--usx-spacing-xs);
  align-items: center;
}

/* ─── Pill base ───────────────────────────────────────────────── */

.frontmatter-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px var(--usx-spacing-sm);
  border: 1px solid var(--usx-color-border);
  border-radius: var(--usx-radius-full);
  background-color: var(--usx-color-surface);
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-xs);
  font-family: var(--usx-font-family-sans);
  cursor: pointer;
  transition: all 120ms ease;
  white-space: nowrap;
}

.frontmatter-pill:hover {
  border-color: var(--usx-color-primary);
  color: var(--usx-color-primary);
}

.frontmatter-pill--tag {
  background-color: color-mix(in srgb, var(--usx-color-info) 12%, transparent);
  border-color: color-mix(in srgb, var(--usx-color-info) 30%, transparent);
  color: var(--usx-color-info);
}

.frontmatter-pill--status .frontmatter-pill__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: var(--usx-color-success);
  flex-shrink: 0;
}

.frontmatter-pill--date {
  color: var(--usx-color-on-surface-muted);
}

.frontmatter-pill--source {
  color: var(--usx-color-primary);
  background-color: color-mix(
    in srgb,
    var(--usx-color-primary) 8%,
    transparent
  );
  border-color: color-mix(in srgb, var(--usx-color-primary) 20%, transparent);
}

.frontmatter-pill--add {
  border-style: dashed;
  color: var(--usx-color-on-surface-muted);
  padding: 2px var(--usx-spacing-xs);
}

.frontmatter-pill--add:hover {
  color: var(--usx-color-primary);
  border-color: var(--usx-color-primary);
  background-color: color-mix(
    in srgb,
    var(--usx-color-primary) 8%,
    transparent
  );
}

/* ─── Inline edit ─────────────────────────────────────────────── */

.frontmatter-pill-edit {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-xs) 0;
}

.frontmatter-pill-edit__key {
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
  font-weight: var(--usx-font-weight-medium);
  flex-shrink: 0;
}

.frontmatter-pill-edit__input {
  padding: 2px var(--usx-spacing-sm);
  border: 1px solid var(--usx-color-primary);
  border-radius: var(--usx-radius-sm);
  background-color: var(--usx-color-background);
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-xs);
  font-family: var(--usx-font-family-sans);
  outline: none;
  min-width: 120px;
}

.frontmatter-pill-edit__delete {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border: none;
  background: transparent;
  cursor: pointer;
  color: var(--usx-color-danger);
  border-radius: var(--usx-radius-sm);
}

.frontmatter-pill-edit__delete:hover {
  background-color: color-mix(
    in srgb,
    var(--usx-color-danger) 10%,
    transparent
  );
}
</style>

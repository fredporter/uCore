<template>
  <div v-if="open" class="fm-editor__backdrop" @click.self="close">
    <section
      ref="dialogEl"
      class="fm-editor"
      role="dialog"
      aria-modal="true"
      aria-labelledby="fm-editor-title"
      @keydown.escape="close"
    >
      <header class="fm-editor__header">
        <div>
          <h2 id="fm-editor-title">Document properties</h2>
          <p>Edit structured fields or the supported YAML subset.</p>
        </div>
        <button type="button" aria-label="Close properties" @click="close">
          <UIcon name="close" />
        </button>
      </header>

      <nav class="fm-editor__tabs" aria-label="Property editor mode">
        <button type="button" :aria-pressed="tab === 'visual'" @click="tab = 'visual'">Fields</button>
        <button type="button" :aria-pressed="tab === 'yaml'" @click="openYaml">YAML</button>
      </nav>

      <div class="fm-editor__presets">
        <span>Template</span>
        <button v-for="preset in presets" :key="preset.id" type="button" @click="applyPreset(preset.id)">
          {{ preset.label }}
        </button>
      </div>

      <div v-if="tab === 'visual'" class="fm-editor__fields">
        <div v-for="(field, index) in fields" :key="field.id" class="fm-editor__field">
          <label>
            <span>Field</span>
            <input v-model.trim="field.key" :aria-label="`Field ${index + 1} name`" />
          </label>
          <label>
            <span>Value</span>
            <input
              v-if="field.kind === 'boolean'"
              type="checkbox"
              :checked="field.value === 'true'"
              :aria-label="`Field ${index + 1} value`"
              @change="field.value = ($event.target as HTMLInputElement).checked ? 'true' : 'false'"
            />
            <input v-else v-model="field.value" :type="fieldType(field.key)" :aria-label="`Field ${index + 1} value`" />
          </label>
          <button type="button" :aria-label="`Remove ${field.key || 'field'}`" @click="removeField(index)">
            <UIcon name="delete" />
          </button>
        </div>
        <button type="button" class="fm-editor__add" @click="addField">Add field</button>
      </div>

      <label v-else class="fm-editor__yaml">
        <span>YAML frontmatter</span>
        <textarea v-model="yamlText" spellcheck="false" @input="validateYamlText" />
      </label>

      <div class="fm-editor__preview">
        <strong>Preview</strong>
        <pre>{{ preview }}</pre>
      </div>
      <ul v-if="errors.length" class="fm-editor__errors" aria-live="polite">
        <li v-for="error in errors" :key="error">{{ error }}</li>
      </ul>

      <footer class="fm-editor__footer">
        <button type="button" @click="close">Cancel</button>
        <button type="button" class="fm-editor__save" :disabled="errors.length > 0" @click="save">Save properties</button>
      </footer>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";
import UIcon from "../../atoms/UIcon.vue";
import {
  stringifyYaml,
  validateYaml,
  type Frontmatter,
} from "../../../utils/frontmatterParser";

interface Props { open: boolean; modelValue: Frontmatter }
interface Field { id: number; key: string; value: string; kind: "string" | "boolean" | "array" }

const props = defineProps<Props>();
const emit = defineEmits<{
  close: [];
  save: [value: Frontmatter];
}>();
const tab = ref<"visual" | "yaml">("visual");
const fields = ref<Field[]>([]);
const yamlText = ref("");
const errors = ref<string[]>([]);
const dialogEl = ref<HTMLElement | null>(null);
let fieldId = 0;

const presets = [
  { id: "note", label: "Note" },
  { id: "research", label: "Research" },
  { id: "post", label: "Post" },
] as const;

function reset(value: Frontmatter) {
  fields.value = Object.entries(value).map(([key, raw]) => ({
    id: ++fieldId,
    key,
    value: Array.isArray(raw) ? raw.join(", ") : String(raw ?? ""),
    kind: Array.isArray(raw) ? "array" : typeof raw === "boolean" ? "boolean" : "string",
  }));
  yamlText.value = stringifyYaml(value);
  errors.value = [];
  tab.value = "visual";
}

watch(
  () => props.open,
  (open) => {
    if (!open) return;
    reset(props.modelValue);
    nextTick(() => dialogEl.value?.focus());
  },
  { immediate: true },
);

function visualValue(): Frontmatter {
  const yaml = fields.value
    .filter((field) => field.key)
    .map((field) => `${field.key}: ${field.kind === "array" || field.value.includes(",") ? `[${field.value}]` : field.value}`)
    .join("\n");
  const result = validateYaml(yaml);
  errors.value = result.errors;
  return result.value;
}

const preview = computed(() => {
  const value = tab.value === "yaml" ? validateYaml(yamlText.value).value : visualValue();
  return `---\n${stringifyYaml(value)}---`;
});

function fieldType(key: string): string {
  return /^(date|created|updated)$/i.test(key) ? "date" : "text";
}
function addField() { fields.value.push({ id: ++fieldId, key: "", value: "", kind: "string" }); }
function removeField(index: number) { fields.value.splice(index, 1); }
function close() { emit("close"); }
function openYaml() {
  yamlText.value = stringifyYaml(visualValue());
  tab.value = "yaml";
  validateYamlText();
}
function validateYamlText() { errors.value = validateYaml(yamlText.value).errors; }
function applyPreset(id: (typeof presets)[number]["id"]) {
  const today = new Date().toISOString().slice(0, 10);
  const values: Record<string, Frontmatter> = {
    note: { title: "Untitled", status: "draft", tags: [] },
    research: { title: "Research", status: "draft", date: today, sources: [] },
    post: { title: "Untitled post", status: "draft", date: today, tags: [] },
  };
  reset(values[id]);
}
function save() {
  const result = tab.value === "yaml" ? validateYaml(yamlText.value) : { value: visualValue(), errors: errors.value };
  errors.value = result.errors;
  if (!errors.value.length) emit("save", result.value);
}
</script>

<style scoped>
.fm-editor__backdrop { position: fixed; inset: 0; z-index: var(--usx-z-index-modal); display: grid; place-items: center; padding: var(--usx-spacing-md); background: color-mix(in srgb, var(--usx-color-on-surface) 45%, transparent); }
.fm-editor { width: min(42rem, 100%); max-height: min(46rem, 90vh); overflow: auto; border: var(--usx-border-width) solid var(--usx-color-border); border-radius: var(--usx-radius-lg); background: var(--usx-color-surface); color: var(--usx-color-on-surface); box-shadow: var(--usx-shadow-lg); }
.fm-editor__header, .fm-editor__footer { display: flex; align-items: center; justify-content: space-between; gap: var(--usx-spacing-md); padding: var(--usx-spacing-md); }
.fm-editor__header { border-bottom: var(--usx-border-width) solid var(--usx-color-border); }
.fm-editor__header h2, .fm-editor__header p { margin: 0; }
.fm-editor__header p { color: var(--usx-color-on-surface-muted); font-size: var(--usx-font-size-sm); }
.fm-editor__tabs, .fm-editor__presets { display: flex; flex-wrap: wrap; gap: var(--usx-spacing-xs); padding: var(--usx-spacing-sm) var(--usx-spacing-md); }
.fm-editor__tabs button[aria-pressed="true"] { border-color: var(--usx-color-primary); color: var(--usx-color-primary); }
.fm-editor__presets span { align-self: center; color: var(--usx-color-on-surface-muted); }
.fm-editor__fields, .fm-editor__yaml, .fm-editor__preview, .fm-editor__errors { margin: 0; padding: var(--usx-spacing-md); }
.fm-editor__field { display: grid; grid-template-columns: minmax(8rem, .7fr) minmax(10rem, 1fr) auto; gap: var(--usx-spacing-sm); margin-bottom: var(--usx-spacing-sm); }
.fm-editor__field label, .fm-editor__yaml { display: grid; gap: var(--usx-spacing-xs); }
.fm-editor input, .fm-editor textarea { width: 100%; box-sizing: border-box; }
.fm-editor__yaml textarea { min-height: 12rem; font-family: var(--usx-font-family-mono); }
.fm-editor__preview pre { max-height: 10rem; overflow: auto; padding: var(--usx-spacing-sm); background: var(--usx-color-surface-variant); }
.fm-editor__errors { color: var(--usx-color-error); }
.fm-editor__footer { border-top: var(--usx-border-width) solid var(--usx-color-border); justify-content: flex-end; }
.fm-editor__save { background: var(--usx-color-primary); color: var(--usx-color-on-primary); }
@media (max-width: 40rem) { .fm-editor__field { grid-template-columns: 1fr auto; } .fm-editor__field label { grid-column: 1; } .fm-editor__field button { grid-column: 2; grid-row: 1 / span 2; } }
</style>

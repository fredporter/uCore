/**
 * @component EditTab — Markdown editor with save-to-binder and undo/redo.
 */
<template>
  <div class="edit-tab">
    <div class="edit-tab__toolbar">
      <span class="edit-tab__binder" v-if="binder">Binder: {{ binder }}</span>
      <button class="uxs-btn" @click="undo" :disabled="historyIndex <= 0">Undo</button>
      <button class="uxs-btn" @click="redo" :disabled="historyIndex >= history.length-1">Redo</button>
    </div>
    <div class="edit-tab__frontmatter">
      <input v-model="fmTitle" placeholder="Title" class="edit-tab__fm-input" />
      <input v-model="fmTags" placeholder="Tags (comma separated)" class="edit-tab__fm-input" />
    </div>
    <textarea
      ref="textareaRef"
      v-model="text"
      class="edit-tab__editor"
      @input="pushHistory"
      placeholder="Write markdown..."
    />
    <div class="edit-tab__footer">
      <button class="uxs-btn" @click="$emit('preview')">Preview</button>
      <button class="uxs-btn uxs-btn--primary" @click="$emit('save', { title: fmTitle, content: text, tags: (fmTags || '').split(',').map(t=>t.trim()).filter(Boolean) })">Save to Binder</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from "vue"

const props = defineProps<{
  content?: string
  binder?: string
  title?: string
  tags?: string[]
}>()

defineEmits<{ preview: []; save: [{ title: string; content: string; tags: string[] }] }>()

const text = ref(props.content || "")
const fmTitle = ref(props.title || "")
const fmTags = ref((props.tags || []).join(", "))
const textareaRef = ref<HTMLTextAreaElement | null>(null)
const history = ref<string[]>([props.content || ""])
const historyIndex = ref(0)

watch(() => props.content, (v) => {
  if (v !== undefined && v !== text.value) {
    text.value = v
    history.value = [v]
    historyIndex.value = 0
  }
})

function pushHistory() {
  if (text.value === history.value[historyIndex.value]) return
  history.value = history.value.slice(0, historyIndex.value + 1)
  history.value.push(text.value)
  historyIndex.value = history.value.length - 1
}

function undo() {
  if (historyIndex.value > 0) {
    historyIndex.value--
    text.value = history.value[historyIndex.value]
  }
}

function redo() {
  if (historyIndex.value < history.value.length - 1) {
    historyIndex.value++
    text.value = history.value[historyIndex.value]
  }
}
</script>

<style scoped>
.edit-tab { display: flex; flex-direction: column; height: 100%; padding: var(--usx-spacing-sm); }
.edit-tab__toolbar { display: flex; align-items: center; gap: var(--usx-spacing-xs); margin-bottom: var(--usx-spacing-xs); }
.edit-tab__binder { font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); margin-right: auto; }
.edit-tab__frontmatter { display: flex; gap: var(--usx-spacing-xs); margin-bottom: var(--usx-spacing-xs); }
.edit-tab__fm-input { flex: 1; min-height: var(--usx-touch-target-compact); padding: 0 var(--usx-spacing-sm); border: var(--usx-border-width) solid var(--usx-color-border); border-radius: var(--usx-radius-sm); font-size: var(--usx-font-size-sm); background: var(--usx-color-surface-variant); }
.edit-tab__editor { flex: 1; min-height: calc(var(--usx-touch-target-comfortable) * 4); padding: var(--usx-spacing-sm); border: var(--usx-border-width) solid var(--usx-color-border); border-radius: var(--usx-radius-sm); font-family: var(--usx-font-family-mono); font-size: var(--usx-font-size-sm); resize: vertical; background: var(--usx-color-surface); }
.edit-tab__footer { display: flex; gap: var(--usx-spacing-xs); margin-top: var(--usx-spacing-xs); }
.uxs-btn { border: var(--usx-border-width) solid var(--usx-color-border); border-radius: var(--usx-radius-sm); min-height: var(--usx-touch-target-compact); padding: 0 var(--usx-spacing-sm); cursor: pointer; background: var(--usx-color-surface); font-size: var(--usx-font-size-xs); }
.uxs-btn:hover { background: var(--usx-color-surface-hover); }
.uxs-btn:disabled { opacity: 0.5; cursor: default; }
.uxs-btn--primary { background: var(--usx-color-primary); color: var(--usx-color-on-primary); border-color: var(--usx-color-primary); }
</style>

<template>
  <div v-if="open" class="dialog-backdrop" @click.self="$emit('close')">
    <section class="dialog" role="dialog" aria-modal="true" aria-labelledby="file-dialog-title">
      <h3 id="file-dialog-title">{{ title }}</h3>
      <p v-if="mode === 'delete'">Delete <code>{{ path }}</code>? Git can recover tracked files, but untracked content may be lost.</p>
      <template v-else>
        <label for="file-path">{{ mode === 'create' ? 'New file path' : 'Destination path' }}</label>
        <input id="file-path" v-model="target" placeholder="src/example.ts" @keydown.enter="submit" />
      </template>
      <p v-if="error" class="dialog__error" role="alert">{{ error }}</p>
      <footer>
        <UButton variant="ghost" @click="$emit('close')">Cancel</UButton>
        <UButton :disabled="busy || (mode !== 'delete' && !target.trim())" @click="submit">{{ mode === 'delete' ? 'Delete file' : 'Apply' }}</UButton>
      </footer>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import UButton from "../../skills/atoms/UButton.vue";

type Mode = "create" | "move" | "delete";
const props = defineProps<{ open: boolean; mode: Mode; repository: string; path: string; revision?: string }>();
const emit = defineEmits<{ close: []; complete: [path: string, deleted: boolean] }>();
const target = ref(""); const error = ref(""); const busy = ref(false);
const title = computed(() => ({ create: "Create file", move: "Rename or move file", delete: "Confirm deletion" })[props.mode]);
watch(() => [props.open, props.mode, props.path], () => { target.value = props.mode === "move" ? props.path : ""; error.value = ""; });
async function submit() {
  busy.value = true; error.value = "";
  try {
    let url = `/api/developer/repos/${encodeURIComponent(props.repository)}/files`;
    let init: RequestInit = { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ path: target.value }) };
    if (props.mode === "move") { url = `/api/developer/repos/${encodeURIComponent(props.repository)}/file-move`; init.body = JSON.stringify({ source: props.path, destination: target.value }); }
    if (props.mode === "delete") { url = `/api/developer/repos/${encodeURIComponent(props.repository)}/file-preview?path=${encodeURIComponent(props.path)}`; init = { method: "DELETE", headers: { "If-Match": props.revision || "" } }; }
    const response = await fetch(url, init); const data = await response.json();
    if (!response.ok) throw new Error(data.error || "File operation failed");
    emit("complete", props.mode === "delete" ? props.path : data.path, props.mode === "delete"); emit("close");
  } catch (cause) { error.value = cause instanceof Error ? cause.message : "File operation failed"; }
  finally { busy.value = false; }
}
</script>

<style scoped>
.dialog-backdrop { position: fixed; inset: 0; z-index: 1000; display: grid; place-items: center; background: rgba(0,0,0,.55); }
.dialog { width: min(30rem, calc(100vw - 2rem)); padding: var(--usx-spacing-md); background: var(--usx-color-surface); color: var(--usx-color-on-surface); border: var(--usx-border-width) solid var(--usx-color-border); border-radius: var(--usx-radius-md); }
.dialog h3 { margin-top: 0; }.dialog label,.dialog input { display: block; width: 100%; }.dialog input { margin-top: var(--usx-spacing-xs); padding: var(--usx-spacing-sm); background: var(--usx-color-background); color: inherit; border: var(--usx-border-width) solid var(--usx-color-border); }.dialog footer { display: flex; justify-content: end; gap: var(--usx-spacing-sm); margin-top: var(--usx-spacing-md); }.dialog__error { color: var(--usx-color-danger); }
</style>

<template>
  <div v-if="activeBinder" class="binder-management" :class="{ 'binder-management--icons': iconOnly }">
      <form v-if="renaming" class="binder-rename" @submit.prevent="saveName">
        <label :for="inputId">Binder name</label>
        <input :id="inputId" v-model="binderName" ref="nameInput" maxlength="200" required :disabled="renameBusy" />
        <button class="usx-btn" :disabled="renameBusy || !binderName.trim()">Save name</button>
        <button type="button" class="usx-btn" :disabled="renameBusy" @click="renaming = false">Cancel</button>
      </form>
      <div v-else class="binder-actions">
        <button type="button" class="usx-btn" :disabled="deleting" aria-label="Rename Binder" title="Rename Binder" @click="beginRename"><UIcon name="edit" aria-hidden="true" /><span v-if="!iconOnly">Rename Binder</span></button>
        <button type="button" class="usx-btn" :disabled="deleting" aria-label="Delete Binder" title="Delete Binder" @click="deleteActiveBinder"><UIcon name="delete" aria-hidden="true" /><span v-if="!iconOnly">Delete Binder</span></button>
      </div>
    <p v-if="notice" role="alert">{{ notice }}</p>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, useId, watch } from "vue";
import { useWorkflowStore } from "../../stores/workflow";
import UIcon from "../atoms/UIcon.vue";

defineProps<{ iconOnly?: boolean }>();
const wf = useWorkflowStore();
const inputId = useId();
const nameInput = ref<HTMLInputElement | null>(null);
const notice = ref("");
const deleting = ref(false);
const activeBinder = computed(() => wf.binders.find(binder => binder.id === wf.activeBinderId));
watch(() => wf.activeBinderId, () => { renaming.value = false; notice.value = ""; });
const renaming = ref(false), renameBusy = ref(false), binderName = ref(""), renameId = ref("");
async function beginRename() {
  notice.value = "";
  renameId.value = wf.activeBinderId;
  binderName.value = wf.binders.find(binder => binder.id === renameId.value)?.title || renameId.value;
  renaming.value = true;
  await nextTick();
  nameInput.value?.focus();
}
async function saveName() {
  if (renameBusy.value || !binderName.value.trim()) return;
  renameBusy.value = true; notice.value = "";
  try {
    await wf.renameBinder(renameId.value, binderName.value.trim());
    renaming.value = false;
  } catch (error) { notice.value = error instanceof Error ? error.message : "Could not rename Binder"; }
  finally { renameBusy.value = false; }
}
async function deleteActiveBinder() {
  const binder = activeBinder.value;
  if (!binder || deleting.value) return;
  if (!window.confirm(`Move “${binder.title || binder.id}” and its documents to Vault/Trash/Binders? Linked tasks will be kept.`)) return;
  deleting.value = true;
  notice.value = "";
  try {
    await wf.deleteBinder(binder.id);
  } catch (error) {
    notice.value = error instanceof Error ? error.message : "Could not delete Binder";
  } finally {
    deleting.value = false;
  }
}
</script>

<style scoped>
.binder-management,
.binder-rename,
.binder-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--usx-spacing-xs);
  min-width: 0;
}

.binder-management p {
  flex-basis: 100%;
  margin: 0;
}

.binder-rename input {
  width: min(100%, 14rem);
}

.binder-management .usx-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  margin: 0;
  padding-inline: var(--usx-spacing-sm);
}

.binder-management--icons .binder-actions .usx-btn {
  justify-content: center;
}
</style>

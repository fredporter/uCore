<template>
  <div class="workflow-dashboard">
    <MissionControlPanel />
    <details :open="binderOpen" class="workflow-dashboard__materials" @toggle="binderOpen = ($event.target as HTMLDetailsElement).open">
      <summary>Binder materials</summary>
      <NotebookBinderPanel v-if="binderOpen" />
    </details>
    <details class="workflow-dashboard__research" @toggle="researchOpen = ($event.target as HTMLDetailsElement).open">
      <summary>Research</summary>
      <BrowserUISurface
        v-if="researchOpen && wf.activeBinderId"
        :key="wf.activeBinderId"
        :binder-id="wf.activeBinderId"
        embedded
      />
      <p v-else-if="researchOpen">Select or create a Binder to collect research.</p>
    </details>
  </div>
</template>
<script setup lang="ts">
import { ref, watch } from 'vue';
import { useWorkflowStore } from '../../../stores/workflow';
import MissionControlPanel from './MissionControlPanel.vue';
import NotebookBinderPanel from './NotebookBinderPanel.vue';
import BrowserUISurface from '../../browserui/BrowserUISurface.vue';
const wf = useWorkflowStore();
const researchOpen = ref(false);
const binderOpen = ref(false);
watch(() => wf.binderCreateRequested, requested => { if (requested) binderOpen.value = true; }, { immediate: true });
</script>
<style scoped>
.workflow-dashboard {
  display: grid;
  align-content: start;
  gap: var(--usx-spacing-md);
  min-width: 0;
}
.workflow-dashboard__research, .workflow-dashboard__materials {
  padding: var(--usx-spacing-md);
  margin: 0;
  border-top: 1px solid var(--usx-color-border);
}
summary {
  cursor: pointer;
  font-size: var(--usx-font-size-lg);
  font-weight: var(--usx-font-weight-semibold);
}
</style>

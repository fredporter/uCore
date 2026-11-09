<template>
  <div class="workflow-dashboard">
    <MissionControlPanel />
    <NotebookBinderPanel />
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
import { ref } from 'vue';
import { useWorkflowStore } from '../../../stores/workflow';
import MissionControlPanel from './MissionControlPanel.vue';
import NotebookBinderPanel from './NotebookBinderPanel.vue';
import BrowserUISurface from '../../browserui/BrowserUISurface.vue';
const wf = useWorkflowStore();
const researchOpen = ref(false);
</script>
<style scoped>
.workflow-dashboard {
  display: grid;
  gap: var(--usx-spacing-md);
  min-width: 0;
}
.workflow-dashboard__research {
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

<template>
  <div class="workflow-dashboard">
    <MissionControlPanel />
    <nav class="workflow-dashboard__cards" aria-label="Mission resources">
      <button class="usx-btn workflow-dashboard__card" type="button"
        :aria-pressed="activePanel === 'binder'" @click="openPanel('binder')">
        <UIcon name="book" />
        <span><strong>Binder materials</strong><small>Review briefs, drafts and sources.</small></span>
        <UIcon name="chevron_right" />
      </button>
      <button class="usx-btn workflow-dashboard__card" type="button"
        :aria-pressed="activePanel === 'research'" @click="openPanel('research')">
        <UIcon name="search" />
        <span><strong>Research</strong><small>Collect findings in a Binder.</small></span>
        <UIcon name="chevron_right" />
      </button>
    </nav>
    <section v-if="activePanel" ref="panel" tabindex="-1" class="workflow-dashboard__panel"
      :aria-label="activePanel === 'binder' ? 'Binder materials' : 'Research'">
      <NotebookBinderPanel v-if="activePanel === 'binder'" />
      <BrowserUISurface v-else-if="wf.activeBinderId" :key="wf.activeBinderId" :binder-id="wf.activeBinderId" embedded />
      <p v-else>Select or create a Binder to collect research.</p>
    </section>
  </div>
</template>

<script setup lang="ts">
import { nextTick, ref, watch } from 'vue';
import { useWorkflowStore } from '../../../stores/workflow';
import UIcon from '../../../skills/atoms/UIcon.vue';
import MissionControlPanel from './MissionControlPanel.vue';
import NotebookBinderPanel from './NotebookBinderPanel.vue';
import BrowserUISurface from '../../browserui/BrowserUISurface.vue';

const wf = useWorkflowStore();
const activePanel = ref<'binder' | 'research' | null>(null);
const panel = ref<HTMLElement | null>(null);

async function openPanel(view: 'binder' | 'research') {
  activePanel.value = view;
  await nextTick();
  panel.value?.focus();
}

watch(() => wf.binderCreateRequested, requested => {
  if (requested) activePanel.value = 'binder';
}, { immediate: true });
</script>

<style scoped>
.workflow-dashboard {
  display: grid;
  align-content: start;
  gap: var(--usx-spacing-md);
  min-width: 0;
}
.workflow-dashboard__cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 16rem), 1fr));
  gap: var(--usx-spacing-sm);
  padding-inline: var(--usx-spacing-md);
}
.workflow-dashboard__card {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: var(--usx-spacing-sm);
  min-width: 0;
  width: 100%;
  margin: 0;
  padding: var(--usx-spacing-md);
  text-align: left;
  white-space: normal;
  background: var(--usx-color-surface);
}
.workflow-dashboard__card[aria-pressed="true"] { border-color: var(--usx-color-primary); }
.workflow-dashboard__card strong, .workflow-dashboard__card small { display: block; line-height: 1.4; }
.workflow-dashboard__card strong { font-size: var(--usx-font-size-base); font-weight: var(--usx-font-weight-semibold); }
.workflow-dashboard__card small { font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); }
.workflow-dashboard__panel { min-width: 0; margin: 0; padding: var(--usx-spacing-md); font-size: var(--usx-font-size-base); }
.workflow-dashboard__panel:focus-visible { outline: 2px solid var(--usx-color-primary); outline-offset: -2px; }
</style>

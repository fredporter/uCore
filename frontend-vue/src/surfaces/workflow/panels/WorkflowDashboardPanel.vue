<template>
  <div class="workflow-dashboard">
    <MissionControlPanel />
    <nav class="workflow-dashboard__cards" aria-label="Mission resources">
      <button
        class="usx-btn workflow-dashboard__card"
        type="button"
        :aria-pressed="activePanel === 'binder'"
        @click="togglePanel('binder')"
      >
        <UIcon name="book" class="workflow-dashboard__card-icon" />
        <span class="workflow-dashboard__card-copy">
          <strong>Binder materials</strong>
          <small>Review briefs, drafts and sources.</small>
        </span>
        <UIcon :name="activePanel === 'binder' ? 'expand_less' : 'chevron_right'" class="workflow-dashboard__card-arrow" />
      </button>
      <button
        class="usx-btn workflow-dashboard__card"
        type="button"
        :aria-pressed="activePanel === 'research'"
        @click="togglePanel('research')"
      >
        <UIcon name="search" class="workflow-dashboard__card-icon" />
        <span class="workflow-dashboard__card-copy">
          <strong>Research</strong>
          <small>Collect findings in a Binder.</small>
        </span>
        <UIcon :name="activePanel === 'research' ? 'expand_less' : 'chevron_right'" class="workflow-dashboard__card-arrow" />
      </button>
    </nav>
    <section
      v-if="activePanel"
      ref="panel"
      tabindex="-1"
      class="workflow-dashboard__panel"
      :aria-label="activePanel === 'binder' ? 'Binder materials' : 'Research'"
    >
      <div class="workflow-dashboard__panel-header">
        <span class="workflow-dashboard__panel-title">
          <UIcon :name="activePanel === 'binder' ? 'book' : 'search'" :size="18" />
          {{ activePanel === 'binder' ? 'Binder materials' : 'Research' }}
        </span>
        <button
          class="usx-btn workflow-dashboard__close-btn"
          type="button"
          aria-label="Close"
          @click="activePanel = null"
        >
          <UIcon name="close" :size="18" />
        </button>
      </div>
      <div class="workflow-dashboard__panel-body">
        <NotebookBinderPanel v-if="activePanel === 'binder'" />
        <BrowserUISurface v-else-if="wf.activeBinderId" :key="wf.activeBinderId" :binder-id="wf.activeBinderId" embedded />
        <div v-else class="workflow-dashboard__empty">
          <UIcon name="info" :size="20" />
          <p>Select or create a Binder to collect research.</p>
        </div>
      </div>
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

async function togglePanel(view: 'binder' | 'research') {
  if (activePanel.value === view) {
    activePanel.value = null;
    return;
  }
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
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
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
  border: 1px solid var(--usx-color-border);
  border-radius: var(--usx-radius-md, 12px);
  cursor: pointer;
  transition: border-color var(--usx-transition-fast, 0.15s ease), background var(--usx-transition-fast, 0.15s ease);
}
.workflow-dashboard__card:hover {
  background: var(--usx-color-surface-hover, var(--usx-color-surface));
  border-color: var(--usx-color-border-light, var(--usx-color-border));
}
.workflow-dashboard__card[aria-pressed="true"] {
  border-color: var(--usx-color-primary);
  background: color-mix(in srgb, var(--usx-color-primary) 6%, var(--usx-color-surface));
}
.workflow-dashboard__card-icon {
  font-size: 22px;
  color: var(--usx-color-primary);
}
.workflow-dashboard__card-copy strong,
.workflow-dashboard__card-copy small {
  display: block;
  line-height: 1.4;
}
.workflow-dashboard__card-copy strong {
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface);
}
.workflow-dashboard__card-copy small {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
}
.workflow-dashboard__card-arrow {
  font-size: 20px;
  color: var(--usx-color-on-surface-muted);
}
.workflow-dashboard__panel {
  min-width: 0;
  margin: 0 var(--usx-spacing-md);
  border: 1px solid var(--usx-color-border);
  border-radius: var(--usx-radius-md, 12px);
  background: var(--usx-color-surface);
  font-size: var(--usx-font-size-base);
  overflow: hidden;
}
.workflow-dashboard__panel:focus-visible {
  outline: 2px solid var(--usx-color-primary);
  outline-offset: -2px;
}
.workflow-dashboard__panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  background: color-mix(in srgb, var(--usx-color-background) 50%, var(--usx-color-surface));
  border-bottom: 1px solid var(--usx-color-border);
}
.workflow-dashboard__panel-title {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface);
}
.workflow-dashboard__close-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 28px;
  padding: 0 6px;
  margin: 0;
  border: 0;
  background: transparent;
  color: var(--usx-color-on-surface-muted);
  box-shadow: none;
}
.workflow-dashboard__close-btn:hover {
  color: var(--usx-color-on-surface);
  background: color-mix(in srgb, var(--usx-color-on-surface) 8%, transparent);
}
.workflow-dashboard__panel-body {
  padding: var(--usx-spacing-md);
}
.workflow-dashboard__empty {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
  margin: var(--usx-spacing-sm) 0;
}
.workflow-dashboard__empty p {
  margin: 0;
}
</style>

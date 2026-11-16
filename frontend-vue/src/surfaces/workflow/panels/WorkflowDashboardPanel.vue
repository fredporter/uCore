<template>
  <div class="workflow-dashboard">
    <MissionControlPanel />
    <div class="workflow-dashboard__cards">
      <button
        class="usx-btn workflow-dashboard__card"
        type="button"
        @click="wf.setTab('binder')"
      >
        <UIcon name="book" class="workflow-dashboard__card-icon" />
        <span class="workflow-dashboard__card-copy">
          <strong>Binder materials</strong>
          <small>Review briefs, drafts and sources.</small>
        </span>
        <UIcon name="chevron_right" class="workflow-dashboard__card-arrow" />
      </button>
      <button
        class="usx-btn workflow-dashboard__card"
        type="button"
        @click="wf.setTab('research')"
      >
        <UIcon name="search" class="workflow-dashboard__card-icon" />
        <span class="workflow-dashboard__card-copy">
          <strong>Research</strong>
          <small>Collect findings in a Binder.</small>
        </span>
        <UIcon name="chevron_right" class="workflow-dashboard__card-arrow" />
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useWorkflowStore } from '../../../stores/workflow';
import UIcon from '../../../skills/atoms/UIcon.vue';
import MissionControlPanel from './MissionControlPanel.vue';

const wf = useWorkflowStore();
</script>

<style scoped>
.workflow-dashboard {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-md);
  min-width: 0;
}
.workflow-dashboard > * {
  flex: 0 0 auto;
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
</style>

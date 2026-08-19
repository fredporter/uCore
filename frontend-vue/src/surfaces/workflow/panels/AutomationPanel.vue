<template>
  <div class="wf-panel">
    <div class="wf-toolbar">
      <span class="wf-toolbar__count">
        <UIcon name="automation" />
        uFlow Automation
      </span>
      <UButton size="sm" variant="secondary" icon="refresh" @click="refresh">
        Refresh
      </UButton>
    </div>

    <div v-if="wf.loading" class="wf-state">Loading workflow automation…</div>
    <div v-else-if="wf.error" class="wf-state wf-state--error">{{ wf.error }}</div>
    <template v-else>
      <section class="wf-section">
        <h4 class="wf-section-title">Definitions</h4>
        <p class="wf-muted">
          Durable definitions are owned by uFlow. Provider and model selection
          is resolved by execution policy when a workflow runs.
        </p>
        <div v-if="wf.workflowDefinitions.length" class="wf-list">
          <article
            v-for="definition in wf.workflowDefinitions"
            :key="definition.id"
            class="wf-card"
          >
            <div>
              <strong>{{ definition.name }}</strong>
              <p>{{ definition.description || "No description" }}</p>
            </div>
            <div class="wf-card__meta">
              <UBadge type="info" size="sm">
                {{ definition.steps.length }} steps
              </UBadge>
              <span>{{ definition.schedule || "manual" }}</span>
            </div>
          </article>
        </div>
        <div v-else class="wf-state">No automation definitions yet.</div>
      </section>

      <section class="wf-section">
        <h4 class="wf-section-title">Recent Runs</h4>
        <div v-if="wf.workflowRuns.length" class="wf-list">
          <article v-for="run in wf.workflowRuns" :key="run.run_id" class="wf-card">
            <div>
              <strong>{{ run.workflow_name }}</strong>
              <p>{{ run.started_at }}</p>
            </div>
            <UBadge :type="run.status === 'completed' ? 'success' : run.status === 'failed' ? 'error' : 'warning'" size="sm">
              {{ run.status }}
            </UBadge>
          </article>
        </div>
        <div v-else class="wf-state">No workflow runs recorded.</div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from "vue";
import UBadge from "../../../skills/atoms/UBadge.vue";
import UButton from "../../../skills/atoms/UButton.vue";
import UIcon from "../../../skills/atoms/UIcon.vue";
import { useWorkflowStore } from "../../../stores/workflow";

const wf = useWorkflowStore();

async function refresh() {
  await Promise.all([wf.fetchWorkflowDefinitions(), wf.fetchWorkflowRuns()]);
}

onMounted(refresh);
</script>

<style scoped>
.wf-panel { display: grid; gap: var(--usx-spacing-lg); overflow: auto; }
.wf-toolbar { display: flex; align-items: center; justify-content: space-between; gap: var(--usx-spacing-md); }
.wf-toolbar__count { display: inline-flex; align-items: center; gap: var(--usx-spacing-xs); font-weight: var(--usx-font-weight-semibold); }
.wf-section { display: grid; gap: var(--usx-spacing-sm); }
.wf-section-title { margin: 0; }
.wf-muted, .wf-card p, .wf-card__meta { margin: 0; color: var(--usx-color-on-surface-muted); font-size: var(--usx-font-size-sm); }
.wf-list { display: grid; gap: var(--usx-spacing-sm); }
.wf-card { display: flex; align-items: center; justify-content: space-between; gap: var(--usx-spacing-md); padding: var(--usx-spacing-md); border: var(--usx-border-width) solid var(--usx-color-border); border-radius: var(--usx-radius-md); background: var(--usx-color-surface); }
.wf-card__meta { display: flex; align-items: center; gap: var(--usx-spacing-sm); }
.wf-state { padding: var(--usx-spacing-lg); color: var(--usx-color-on-surface-muted); border: var(--usx-border-width) dashed var(--usx-color-border); border-radius: var(--usx-radius-md); }
.wf-state--error { color: var(--usx-color-error); }
</style>

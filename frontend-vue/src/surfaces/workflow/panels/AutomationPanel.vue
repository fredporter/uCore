<template>
  <div class="wf-panel wf-zen-surface">
    <header class="wf-standard-header">
      <div>
        <p class="wf-standard-header__kicker">User Workflow</p>
        <h2>Automation</h2>
        <p>Run dependable routines without adding noise to your day.</p>
      </div>
      <button class="wf-standard-header__action" type="button" @click="refresh"><UIcon name="refresh" /> Refresh</button>
    </header>

    <div v-if="wf.loading" class="wf-state">Loading workflow automation…</div>
    <div v-else-if="wf.error && !definitions.length" class="wf-state wf-state--error">{{ wf.error }}</div>
    <section v-if="selectedDefinition" class="wf-section" role="region" aria-label="Routine details">
      <h3>{{ selectedDefinition.name }}</h3>
      <p>{{ selectedDefinition.description }}</p>
      <pre>{{ JSON.stringify(selectedDefinition.steps, null, 2) }}</pre>
      <UButton variant="secondary" @click="selectedDefinition = null">Close</UButton>
    </section>
    <template v-else>
      <section class="wf-section">
        <header class="wf-section-intro">
          <h4 class="wf-section-title">Definitions</h4>
          <p class="wf-muted">Available routines.</p>
        </header>
        <p v-if="!definitions.length" class="wf-state">No routines configured.</p>
        <div class="wf-list">
          <article
            v-for="definition in definitions"
            :key="definition.id"
            class="wf-card"
          >
            <div class="wf-card__body">
              <strong>{{ definition.name }}</strong>
              <p class="wf-card__detail">{{ definition.description || "No description" }} · {{ definition.steps.length }} steps · {{ definition.schedule || "manual" }}</p>
            </div>
            <button class="wf-canonical-action" type="button" :title="`Open ${definition.name}`" @click="selectedDefinition = definition"><UIcon name="view_sidebar" /></button>
          </article>
        </div>
      </section>

      <section class="wf-section">
        <header class="wf-section-intro">
          <h4 class="wf-section-title">Recent Runs</h4>
          <p class="wf-muted">Latest automation activity and outcomes.</p>
        </header>
        <div v-if="wf.workflowRuns.length" class="wf-list">
          <article v-for="run in wf.workflowRuns" :key="run.run_id" class="wf-card">
            <div class="wf-card__body">
              <strong>{{ run.workflow_name }}</strong>
              <p class="wf-card__detail">{{ run.started_at }}</p>
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
import { computed, onMounted, ref } from "vue";
import UBadge from "../../../skills/atoms/UBadge.vue";
import UButton from "../../../skills/atoms/UButton.vue";
import UIcon from "../../../skills/atoms/UIcon.vue";
import { useWorkflowStore } from "../../../stores/workflow";

const wf = useWorkflowStore();
const definitions = computed(() => wf.workflowDefinitions);
const selectedDefinition = ref<(typeof wf.workflowDefinitions)[number] | null>(null);

async function refresh() {
  await Promise.all([wf.fetchWorkflowDefinitions(), wf.fetchWorkflowRuns()]);
}

onMounted(refresh);
</script>

<style scoped>
.wf-panel { display: grid; gap: var(--usx-spacing-xl); overflow: auto; width: min(100%, 60rem); margin: 0 auto; padding: clamp(var(--usx-spacing-md), 4vw, var(--usx-spacing-2xl)); align-content: start; }
.wf-section { display: grid; gap: var(--usx-spacing-sm); padding-top: var(--usx-spacing-lg); border-top: var(--usx-border-width) solid var(--usx-color-border); }
.wf-section-title { margin: 0; }
.wf-section-intro { padding: var(--usx-spacing-sm) var(--usx-spacing-xs); }
.wf-section-intro .wf-muted { margin-top: 2px; }
.wf-muted, .wf-card p, .wf-card__meta { margin: 0; color: var(--usx-color-on-surface-muted); font-size: var(--usx-font-size-sm); }
.wf-list { display: grid; gap: var(--usx-spacing-sm); }
.wf-card { display: flex; align-items: center; justify-content: space-between; gap: var(--usx-spacing-md); min-height: 4rem; padding: var(--usx-spacing-sm) var(--usx-spacing-xs); border: 0; border-bottom: var(--usx-border-width) solid var(--usx-color-border); background: transparent; }
.wf-card__meta { display: flex; align-items: center; gap: var(--usx-spacing-sm); }
.wf-state { padding: var(--usx-spacing-lg); color: var(--usx-color-on-surface-muted); border: var(--usx-border-width) dashed var(--usx-color-border); border-radius: var(--usx-radius-md); }
.wf-state--error { color: var(--usx-color-error); }
.wf-starter { color: var(--usx-color-primary); }
</style>

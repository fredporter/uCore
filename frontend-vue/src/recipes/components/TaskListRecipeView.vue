<script setup lang="ts">
import { computed, ref } from 'vue'
import UIcon from '../../skills/atoms/UIcon.vue'
import type { TaskListItem, TaskListRecipe } from '../recipes'

const props = defineProps<{ recipe: TaskListRecipe }>()
const view = ref<'board' | 'rows'>('board')
const statuses = {
  pending: { label: 'To do', icon: 'radio_button_unchecked' },
  in_progress: { label: 'In progress', icon: 'pending' },
  failed: { label: 'Blocked', icon: 'error' },
  completed: { label: 'Done', icon: 'check_circle' },
} satisfies Record<TaskListItem['status'], { label: string; icon: string }>

const lanes = computed(() => Object.entries(statuses).map(([status, details]) => ({
  status,
  ...details,
  items: props.recipe.items.filter(item => item.status === status),
})))
</script>

<template>
  <section class="task-preview" aria-label="Workflow recipe preview">
    <header class="preview-header">
      <div class="preview-title-card">
        <h2>{{ recipe.title }}</h2>
        <p>{{ recipe.description }}</p>
      </div>
      <div class="view-controls" aria-label="Task preview view" role="group">
        <button type="button" class="usx-btn" :aria-pressed="view === 'board'" @click="view = 'board'">
          <UIcon name="view_kanban" /> Board
        </button>
        <button type="button" class="usx-btn" :aria-pressed="view === 'rows'" @click="view = 'rows'">
          <UIcon name="table_rows" /> Rows
        </button>
      </div>
    </header>

    <div class="lanes" :class="{ 'lanes--rows': view === 'rows' }">
      <section v-for="lane in lanes" :key="lane.status" class="lane" :class="'lane--' + lane.status">
        <h3 class="lane-title">
          <UIcon :name="lane.icon" />
          {{ lane.label }}
          <span>{{ lane.items.length }}</span>
        </h3>
        <p v-if="!lane.items.length" class="empty-lane">No tasks</p>
        <article v-for="item in lane.items" :key="item.id" class="task-card">
          <h4>{{ item.title }}</h4>
          <p v-if="item.subtitle">{{ item.subtitle }}</p>
          <span v-if="item.badge" class="priority">{{ item.badge }}</span>
        </article>
      </section>
    </div>

    <details v-if="recipe.variableExamples?.length" class="variable-examples">
      <summary>System variable examples</summary>
      <dl>
        <div v-for="example in recipe.variableExamples" :key="example.name">
          <dt><code>{{ example.name }}</code></dt>
          <dd>{{ example.label }}</dd>
        </div>
      </dl>
    </details>
  </section>
</template>

<style scoped>
.task-preview {
  display: grid;
  padding: 0;
  gap: var(--usx-spacing-sm);
  color: var(--usx-color-on-surface);
}

.view-controls, .lane-title {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
}

.preview-header {
  display: grid;
  gap: var(--usx-spacing-sm);
}

.view-controls[role="group"] {
  justify-content: center;
  flex-wrap: wrap;
  margin: 0;
  padding: 0;
  border: 0;
  outline: none;
  box-shadow: none;
}

.preview-title-card {
  display: grid;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  background: var(--usx-color-surface);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
}

.preview-title-card h2 {
  font-size: var(--usx-font-size-xl);
}

.preview-header h2, .preview-header p, .lane-title, .task-card h4, .task-card p {
  margin: 0;
}

.preview-header p, .task-card p, .empty-lane, .lane-title span {
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
}

.view-controls .usx-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--usx-spacing-xs);
  flex: 0 0 auto;
  width: auto;
  min-width: 6rem;
  min-height: var(--usx-touch-min-sm);
  margin: 0;
  padding: 0 var(--usx-spacing-sm);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface);
}

.view-controls .usx-btn:hover,
.view-controls .usx-btn[aria-pressed="true"] {
  background: var(--usx-color-surface-hover);
}

.view-controls .usx-btn[aria-pressed="true"] {
  color: var(--usx-color-primary);
}

.view-controls .usx-btn:focus {
  outline: none;
  box-shadow: none;
}

.view-controls .usx-btn:focus-visible {
  outline: var(--usx-border-width) dashed var(--usx-color-on-surface);
  outline-offset: calc(-1 * var(--usx-spacing-xs));
}

.lanes {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--usx-spacing-sm);
}

.lanes--rows {
  grid-template-columns: 1fr;
}

.lane {
  --lane-accent: var(--usx-color-border);
  display: grid;
  align-content: start;
  gap: var(--usx-spacing-sm);
  min-width: 0;
  padding: var(--usx-spacing-sm);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-top: var(--usx-border-width-thick) solid var(--lane-accent);
  background: var(--usx-color-surface);
  border-radius: var(--usx-radius-sm);
}

.lane--in_progress { --lane-accent: var(--usx-color-primary); }
.lane--failed { --lane-accent: var(--usx-color-danger); }
.lane--completed { --lane-accent: var(--usx-color-success); }

.lane-title, .task-card h4 {
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-semibold);
}

.lane-title span { margin-inline-start: auto; }

.task-card, .variable-examples {
  padding: var(--usx-spacing-sm);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: var(--usx-color-surface);
  overflow-wrap: anywhere;
}

.task-card { background: var(--usx-color-surface-hover); }

.task-card p { margin-top: var(--usx-spacing-xs); }
.priority { color: var(--usx-color-on-surface); font-size: var(--usx-font-size-xs); }

.variable-examples summary {
  display: list-item;
  min-height: var(--usx-touch-min-sm);
  align-content: center;
  cursor: pointer;
  color: var(--usx-color-on-surface);
}

.variable-examples dl {
  display: flex;
  flex-wrap: wrap;
  gap: var(--usx-spacing-md);
  margin: 0;
}

.variable-examples code {
  background: var(--usx-color-background);
  color: var(--usx-color-on-surface);
}

.variable-examples dd { margin: 0; color: var(--usx-color-on-surface-muted); }

.task-preview { container-type: inline-size; }

@container (max-width: 850px) {
  .lanes:not(.lanes--rows) { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@container (max-width: 460px) {
  .lanes:not(.lanes--rows) { grid-template-columns: 1fr; }
}
</style>

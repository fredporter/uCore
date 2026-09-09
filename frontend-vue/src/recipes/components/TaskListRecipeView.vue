<script setup lang="ts">
import type { TaskListRecipe } from '../recipes'

defineProps<{
  recipe: TaskListRecipe
}>()
</script>

<template>
  <div class="task-list-recipe-container">
    <div class="recipe-header">
      <div class="header-left">
        <span class="material-symbols-outlined header-icon">checklist</span>
        <div>
          <h2 class="recipe-title">{{ recipe.title }}</h2>
          <p class="recipe-desc">{{ recipe.description }}</p>
        </div>
      </div>
      <div class="header-meta">
        <span class="recipe-tag">Recipe: {{ recipe.recipe }}</span>
        <span class="recipe-tag">Cols: {{ recipe.columns }} (Linear)</span>
      </div>
    </div>

    <div class="task-items-flow">
      <div
        v-for="item in recipe.items"
        :key="item.id"
        class="task-item-card"
        :class="[`status-${item.status}`]"
      >
        <div class="task-item-icon-col">
          <span v-if="item.status === 'completed'" class="material-symbols-outlined status-icon icon-done">check_circle</span>
          <span v-else-if="item.status === 'in_progress'" class="material-symbols-outlined status-icon icon-progress">sync</span>
          <span v-else-if="item.status === 'failed'" class="material-symbols-outlined status-icon icon-fail">error</span>
          <span v-else class="material-symbols-outlined status-icon icon-pending">radio_button_unchecked</span>
        </div>

        <div class="task-item-body">
          <div class="task-title-row">
            <span class="task-title">{{ item.title }}</span>
            <span v-if="item.badge" class="task-badge">{{ item.badge }}</span>
          </div>
          <p v-if="item.subtitle" class="task-subtitle">{{ item.subtitle }}</p>

          <div class="task-footer">
            <div class="task-tags" v-if="item.tags?.length">
              <span v-for="tag in item.tags" :key="tag" class="task-tag-pill">#{{ tag }}</span>
            </div>
            <span class="task-timestamp" v-if="item.timestamp">{{ item.timestamp }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.task-list-recipe-container {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  width: 100%;
}

.recipe-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--usx-color-outline-variant, rgba(255, 255, 255, 0.1));
  flex-wrap: wrap;
  gap: 0.75rem;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.header-icon {
  font-size: 28px;
  color: var(--usx-color-primary, #a8c7fa);
}

.recipe-title {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--usx-color-on-surface, #e2e2e6);
}

.recipe-desc {
  margin: 0.25rem 0 0;
  font-size: 0.85rem;
  color: var(--usx-color-on-surface-variant, #8e9199);
}

.header-meta {
  display: flex;
  gap: 0.5rem;
}

.recipe-tag {
  font-size: 0.75rem;
  padding: 0.25rem 0.6rem;
  background: var(--usx-color-surface-container, rgba(255, 255, 255, 0.06));
  border-radius: 4px;
  color: var(--usx-color-on-surface-variant, #c4c6d0);
  font-family: var(--usx-font-family-mono, monospace);
}

/* Linear Single-Column Task Items */
.task-items-flow {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  width: 100%;
}

.task-item-card {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1rem;
  border-radius: 10px;
  background: var(--usx-color-surface-container, rgba(255, 255, 255, 0.03));
  border: 1px solid var(--usx-color-outline-variant, rgba(255, 255, 255, 0.08));
  transition: background 0.15s ease, border-color 0.15s ease;
}

.task-item-card:hover {
  background: var(--usx-color-surface-container-high, rgba(255, 255, 255, 0.06));
  border-color: var(--usx-color-outline, rgba(255, 255, 255, 0.18));
}

.task-item-icon-col {
  padding-top: 2px;
}

.status-icon {
  font-size: 22px;
}
.icon-done { color: #3fb950; }
.icon-progress {
  color: #58a6ff;
  animation: spin 3s linear infinite;
}
.icon-fail { color: #f85149; }
.icon-pending { color: var(--usx-color-on-surface-variant, #8e9199); }

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.task-item-body {
  flex: 1;
  min-width: 0;
}

.task-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.task-title {
  font-weight: 500;
  font-size: 0.95rem;
  color: var(--usx-color-on-surface, #e2e2e6);
}

.task-badge {
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  padding: 0.15rem 0.5rem;
  border-radius: 12px;
  background: rgba(168, 199, 250, 0.15);
  color: #a8c7fa;
  letter-spacing: 0.03em;
}

.task-subtitle {
  margin: 0.35rem 0 0.65rem;
  font-size: 0.85rem;
  color: var(--usx-color-on-surface-variant, #9aa0a6);
  line-height: 1.4;
}

.task-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.75rem;
  gap: 0.5rem;
}

.task-tags {
  display: flex;
  gap: 0.35rem;
  flex-wrap: wrap;
}

.task-tag-pill {
  padding: 0.15rem 0.45rem;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.05);
  color: var(--usx-color-on-surface-variant, #8e9199);
}

.task-timestamp {
  color: var(--usx-color-on-surface-variant, #6e7681);
}
</style>

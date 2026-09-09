<script setup lang="ts">
import type { CardMatrixRecipe } from '../recipes'

defineProps<{
  recipe: CardMatrixRecipe
}>()
</script>

<template>
  <div class="card-matrix-container">
    <div class="recipe-header">
      <div class="header-left">
        <span class="material-symbols-outlined header-icon">dashboard</span>
        <div>
          <h2 class="recipe-title">{{ recipe.title }}</h2>
          <p class="recipe-desc">{{ recipe.description }}</p>
        </div>
      </div>
      <span class="recipe-badge">M3 Tonal Cards</span>
    </div>

    <div class="matrix-grid">
      <div
        v-for="card in recipe.cards"
        :key="card.id"
        class="matrix-card"
      >
        <div class="card-top-row">
          <div class="icon-avatar">
            <span class="material-symbols-outlined">{{ card.icon }}</span>
          </div>
          <span v-if="card.tag" class="card-tag">{{ card.tag }}</span>
        </div>

        <h3 class="card-title">{{ card.title }}</h3>
        <p class="card-description">{{ card.description }}</p>

        <div class="card-footer">
          <span v-if="card.metric" class="card-metric">{{ card.metric }}</span>
          <div class="card-actions" v-if="card.actions?.length">
            <button
              v-for="action in card.actions"
              :key="action.label"
              class="m3-button"
              :class="{ 'm3-button-primary': action.primary }"
            >
              {{ action.label }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.card-matrix-container {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
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

.recipe-badge {
  font-size: 0.75rem;
  padding: 0.25rem 0.6rem;
  background: var(--usx-color-surface-container, rgba(255, 255, 255, 0.06));
  border-radius: 4px;
  color: var(--usx-color-on-surface-variant, #c4c6d0);
  font-family: var(--usx-font-family-mono, monospace);
}

.matrix-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1rem;
  width: 100%;
}

.matrix-card {
  display: flex;
  flex-direction: column;
  padding: 1.25rem;
  border-radius: 12px;
  background: var(--usx-color-surface-container, rgba(255, 255, 255, 0.04));
  border: 1px solid var(--usx-color-outline-variant, rgba(255, 255, 255, 0.08));
  transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;
}

.matrix-card:hover {
  background: var(--usx-color-surface-container-high, rgba(255, 255, 255, 0.07));
  border-color: var(--usx-color-outline, rgba(255, 255, 255, 0.2));
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
}

.card-top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.icon-avatar {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: rgba(168, 199, 250, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--usx-color-primary, #a8c7fa);
}

.icon-avatar .material-symbols-outlined {
  font-size: 22px;
}

.card-tag {
  font-size: 0.7rem;
  padding: 0.2rem 0.5rem;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.06);
  color: var(--usx-color-on-surface-variant, #c4c6d0);
  font-weight: 500;
}

.card-title {
  margin: 0 0 0.5rem;
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--usx-color-on-surface, #e2e2e6);
}

.card-description {
  margin: 0 0 1.25rem;
  font-size: 0.85rem;
  line-height: 1.45;
  color: var(--usx-color-on-surface-variant, #9aa0a6);
  flex: 1;
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 0.75rem;
  border-top: 1px solid var(--usx-color-outline-variant, rgba(255, 255, 255, 0.06));
}

.card-metric {
  font-size: 0.78rem;
  font-family: var(--usx-font-family-mono, monospace);
  color: #3fb950;
  font-weight: 600;
}

.card-actions {
  display: flex;
  gap: 0.5rem;
}

.m3-button {
  padding: 0.35rem 0.75rem;
  font-size: 0.8rem;
  font-weight: 500;
  border-radius: 6px;
  border: 1px solid var(--usx-color-outline-variant, rgba(255, 255, 255, 0.15));
  background: transparent;
  color: var(--usx-color-on-surface, #e2e2e6);
  cursor: pointer;
  transition: background 0.15s ease;
}

.m3-button:hover {
  background: rgba(255, 255, 255, 0.08);
}

.m3-button-primary {
  background: var(--usx-color-primary, #a8c7fa);
  color: #041e49;
  border-color: transparent;
  font-weight: 600;
}

.m3-button-primary:hover {
  background: #c2e7ff;
}
</style>

<template>
  <div class="system-recipe-container">
    <div class="system-header-meta">
      <span class="system-tag">USX Recipe: {{ recipe.recipe }}</span>
      <span class="system-tag">Layout: System Page Shell</span>
      <span class="system-tag">Spec Code: {{ recipe.code }}</span>
    </div>

    <!-- System Page Shell (Exact /system/s100 structure) -->
    <div class="system-page-shell">
      <div class="system-page-header">
        <UIcon :name="recipe.icon || 'search_off'" class="system-page-header-icon" />
        <h2 class="system-page-title">{{ recipe.heading }}</h2>
        <UBadge type="neutral" size="sm">{{ recipe.code }}</UBadge>
      </div>

      <div class="system-page-body">
        <p class="system-page-note">{{ recipe.summary }}</p>

        <!-- Fallback Diagnostic Steps Block -->
        <section v-if="recipe.steps?.length" class="system-fallback-block">
          <h4 class="system-fallback-subtitle">Recommended Actions</h4>
          <ol class="system-fallback-list">
            <li v-for="(step, idx) in recipe.steps" :key="idx">{{ step }}</li>
          </ol>
        </section>

        <!-- Suggested Links Section -->
        <section v-if="recipe.suggestions?.length" class="system-fallback-block">
          <h4 class="system-fallback-subtitle">Suggested Alternative Pages</h4>
          <div class="system-fallback-links">
            <a
              v-for="sug in recipe.suggestions"
              :key="sug.label"
              class="system-fallback-link"
              :href="sug.to"
            >
              {{ sug.label }}
            </a>
          </div>
        </section>

        <!-- Action Row -->
        <div class="system-actions-row">
          <button
            v-for="act in recipe.actions"
            :key="act.label"
            class="system-page-action"
            :class="{ 'system-page-action--primary': act.variant === 'primary' }"
            @click="handleAction(act.action)"
          >
            {{ act.label }}
          </button>
        </div>

        <p v-if="recipe.footnote" class="system-fallback-footnote">{{ recipe.footnote }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { SystemPageRecipe } from '../recipes'
import UIcon from '../../skills/atoms/UIcon.vue'
import UBadge from '../../skills/atoms/UBadge.vue'

defineProps<{
  recipe: SystemPageRecipe
}>()

function handleAction(action: string) {
  if (action === 'retry') {
    alert('Retrying system diagnostic check: All local health endpoints responding.')
  } else if (action === 'back') {
    window.history.back()
  } else if (action === 'home') {
    window.location.href = '/'
  }
}
</script>

<style scoped>
.system-recipe-container {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  width: 100%;
}

.system-header-meta {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.system-tag {
  font-size: 0.75rem;
  padding: 0.25rem 0.6rem;
  background: var(--usx-color-surface-variant, rgba(255, 255, 255, 0.08));
  border-radius: 4px;
  color: var(--usx-color-on-surface-muted, #999);
  font-family: var(--usx-font-family-mono, monospace);
}

/* Authentic /system/s100 System Page Shell */
.system-page-shell {
  width: 100%;
  max-width: 820px;
  margin: 0 auto;
  border: 1px solid var(--usx-color-border, rgba(255, 255, 255, 0.15));
  border-radius: var(--usx-radius-lg, 12px);
  background: var(--usx-color-surface, #1e1e1e);
  padding: var(--usx-spacing-xl, 2rem);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
}

.system-page-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--usx-spacing-sm, 0.75rem);
  margin-bottom: var(--usx-spacing-lg, 1.5rem);
  text-align: center;
}

.system-page-header-icon {
  font-size: 2.5rem;
  color: var(--usx-color-primary, #646cff);
}

.system-page-title {
  margin: 0;
  font-size: var(--usx-font-size-xl, 1.4rem);
  font-weight: var(--usx-font-weight-semibold, 600);
  color: var(--usx-color-on-surface, #fff);
}

.system-page-note {
  color: var(--usx-color-on-surface-muted, #aaa);
  font-size: var(--usx-font-size-base, 1rem);
  margin: 0;
  text-align: center;
  line-height: 1.5;
}

.system-page-body {
  margin-top: var(--usx-spacing-md, 1rem);
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-md, 1rem);
  align-items: center;
}

.system-fallback-block {
  width: 100%;
  border: 1px solid var(--usx-color-border, rgba(255, 255, 255, 0.12));
  border-radius: var(--usx-radius-md, 8px);
  background: var(--usx-color-surface-variant, rgba(255, 255, 255, 0.03));
  padding: var(--usx-spacing-md, 1.25rem);
}

.system-fallback-subtitle {
  margin: 0 0 var(--usx-spacing-sm, 0.75rem);
  font-size: var(--usx-font-size-sm, 0.85rem);
  font-weight: var(--usx-font-weight-semibold, 600);
  color: var(--usx-color-on-surface, #fff);
}

.system-fallback-list {
  margin: 0;
  padding-left: var(--usx-spacing-lg, 1.5rem);
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs, 0.4rem);
  color: var(--usx-color-on-surface-muted, #ccc);
  font-size: var(--usx-font-size-sm, 0.9rem);
  line-height: 1.45;
}

.system-fallback-links {
  display: flex;
  flex-wrap: wrap;
  gap: var(--usx-spacing-sm, 0.5rem);
}

.system-fallback-link {
  border: 1px solid var(--usx-color-border, rgba(255, 255, 255, 0.2));
  background: var(--usx-color-surface, rgba(0, 0, 0, 0.2));
  color: var(--usx-color-on-surface, #fff);
  border-radius: var(--usx-radius-sm, 4px);
  padding: 0.35rem 0.75rem;
  font-size: var(--usx-font-size-sm, 0.85rem);
  text-decoration: none;
  cursor: pointer;
  transition: all 150ms ease;
}

.system-fallback-link:hover {
  border-color: var(--usx-color-primary, #646cff);
  color: var(--usx-color-primary, #646cff);
}

.system-actions-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--usx-spacing-sm, 0.75rem);
  justify-content: center;
  margin-top: 0.5rem;
}

.system-page-action {
  padding: 0.5rem 1.25rem;
  border: 1px solid var(--usx-color-border, rgba(255, 255, 255, 0.2));
  border-radius: var(--usx-radius-sm, 6px);
  background: var(--usx-color-surface-variant, #2a2a2a);
  color: var(--usx-color-on-surface, #fff);
  cursor: pointer;
  font-size: var(--usx-font-size-sm, 0.9rem);
  font-weight: 500;
  transition: all 150ms ease;
}

.system-page-action:hover {
  border-color: var(--usx-color-primary, #646cff);
  color: var(--usx-color-primary, #646cff);
}

.system-page-action--primary {
  background: var(--usx-color-primary, #646cff);
  border-color: var(--usx-color-primary, #646cff);
  color: #fff;
}

.system-page-action--primary:hover {
  background: var(--usx-color-primary-hover, #535bf2);
  color: #fff;
}

.system-fallback-footnote {
  margin: var(--usx-spacing-sm, 0.5rem) 0 0;
  color: var(--usx-color-on-surface-muted, #777);
  font-size: var(--usx-font-size-sm, 0.8rem);
  text-align: center;
}
</style>

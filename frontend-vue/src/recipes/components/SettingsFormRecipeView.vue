<script setup lang="ts">
import { ref } from 'vue'
import type { SettingsFormRecipe } from '../recipes'

const props = defineProps<{
  recipe: SettingsFormRecipe
}>()

// Track local values for interactivity in the preview
const formValues = ref<Record<string, any>>({})
props.recipe.sections.forEach(sec => {
  sec.fields.forEach(f => {
    formValues.value[f.id] = f.value
  })
})
</script>

<template>
  <div class="settings-form-container">
    <div class="recipe-header">
      <div class="header-left">
        <span class="material-symbols-outlined header-icon">tune</span>
        <div>
          <h2 class="recipe-title">{{ recipe.title }}</h2>
          <p class="recipe-desc">{{ recipe.description }}</p>
        </div>
      </div>
      <span class="recipe-badge">M3 Settings</span>
    </div>

    <div class="sections-stack">
      <div
        v-for="section in recipe.sections"
        :key="section.id"
        class="settings-section-card"
      >
        <h3 class="section-title">{{ section.title }}</h3>

        <div class="fields-list">
          <div
            v-for="field in section.fields"
            :key="field.id"
            class="field-row"
          >
            <div class="field-info">
              <label :for="field.id" class="field-label">{{ field.label }}</label>
              <span v-if="field.helpText" class="field-help">{{ field.helpText }}</span>
            </div>

            <div class="field-control">
              <!-- Toggle switch -->
              <label v-if="field.type === 'toggle'" class="m3-switch">
                <input
                  :id="field.id"
                  type="checkbox"
                  v-model="formValues[field.id]"
                />
                <span class="slider round"></span>
              </label>

              <!-- Select control -->
              <select
                v-else-if="field.type === 'select'"
                :id="field.id"
                class="m3-select"
                v-model="formValues[field.id]"
              >
                <option v-for="opt in field.options" :key="opt" :value="opt">
                  {{ opt }}
                </option>
              </select>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.settings-form-container {
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

.sections-stack {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.settings-section-card {
  padding: 1.25rem;
  border-radius: 12px;
  background: var(--usx-color-surface-container, rgba(255, 255, 255, 0.03));
  border: 1px solid var(--usx-color-outline-variant, rgba(255, 255, 255, 0.08));
}

.section-title {
  margin: 0 0 1rem;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--usx-color-primary, #a8c7fa);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.fields-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.field-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding-bottom: 0.85rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}

.field-row:last-child {
  padding-bottom: 0;
  border-bottom: none;
}

.field-info {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  max-width: 70%;
}

.field-label {
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--usx-color-on-surface, #e2e2e6);
}

.field-help {
  font-size: 0.8rem;
  color: var(--usx-color-on-surface-variant, #8e9199);
  line-height: 1.35;
}

/* M3 Switch Toggle */
.m3-switch {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
}

.m3-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0; left: 0; right: 0; bottom: 0;
  background-color: rgba(255, 255, 255, 0.15);
  transition: .2s;
}

.slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: .2s;
}

input:checked + .slider {
  background-color: var(--usx-color-primary, #a8c7fa);
}

input:checked + .slider:before {
  transform: translateX(20px);
  background-color: #041e49;
}

.slider.round {
  border-radius: 24px;
}
.slider.round:before {
  border-radius: 50%;
}

/* M3 Select */
.m3-select {
  padding: 0.4rem 0.8rem;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid var(--usx-color-outline-variant, rgba(255, 255, 255, 0.15));
  color: var(--usx-color-on-surface, #e2e2e6);
  font-size: 0.85rem;
}
</style>

<script setup lang="ts">
import { ref } from 'vue'
import type { SettingsFormRecipe } from '../recipes'

const props = defineProps<{ recipe: SettingsFormRecipe }>()
const fields = props.recipe.sections.flatMap(section => section.fields)
const values = ref(Object.fromEntries(fields.map(field => [field.id, field.value])))
const message = ref('')

function save() {
  if (fields.some(field => field.required && !String(values.value[field.id]).trim())) {
    message.value = 'Enter a value for each required field.'
    return
  }
  message.value = 'Saved for this preview.'
}
</script>

<template>
  <form class="settings-preview" @submit.prevent="save" @input="message = ''">
    <header>
      <h2>{{ recipe.title }}</h2>
      <p>{{ recipe.description }}</p>
    </header>
    <fieldset v-for="section in recipe.sections" :key="section.id">
      <legend>{{ section.title }}</legend>
      <div v-for="field in section.fields" :key="field.id" class="field">
        <label :for="field.id">
          {{ field.label }} <code v-if="field.variable">{{ field.variable }}</code>
        </label>
        <select v-if="field.type === 'select'" :id="field.id" v-model="values[field.id]" :required="field.required">
          <option v-for="option in field.options" :key="option">{{ option }}</option>
        </select>
        <input v-else :id="field.id" v-model="values[field.id]"
          :type="field.type === 'toggle' ? 'checkbox' : field.type === 'slider' ? 'range' : 'text'"
          :required="field.required" :min="field.min" :max="field.max">
        <small v-if="field.helpText">{{ field.helpText }}</small>
      </div>
    </fieldset>
    <div class="form-actions">
      <button type="submit" class="usx-btn usx-btn--primary">Save preview</button>
      <span role="status">{{ message }}</span>
    </div>
  </form>
</template>

<style scoped>
.settings-preview {
  display: grid;
  gap: var(--usx-spacing-md);
  padding: var(--usx-spacing-md);
  color: var(--usx-color-on-surface);
}
h2, p { margin: 0; }
p, small { color: var(--usx-color-on-surface-muted); }
fieldset, .field { display: grid; gap: var(--usx-spacing-xs); min-width: 0; }
fieldset {
  padding: var(--usx-spacing-md);
  gap: var(--usx-spacing-md);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: var(--usx-color-surface);
}
input:not([type="checkbox"]), select {
  width: 100%;
  min-height: var(--usx-touch-min);
  background: var(--usx-color-background);
  color: var(--usx-color-on-surface);
  border-color: var(--usx-color-border);
}
code {
  background: var(--usx-color-background);
  color: var(--usx-color-on-surface-muted);
  white-space: nowrap;
}
.form-actions { display: flex; flex-wrap: wrap; align-items: center; gap: var(--usx-spacing-sm); }
</style>

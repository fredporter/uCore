<script setup lang="ts">
import type { ProseDocumentRecipe } from '../recipes'

defineProps<{
  recipe: ProseDocumentRecipe
}>()
</script>

<template>
  <div class="prose-recipe-container usx-prose">
    <!-- Frontmatter Metadata Bar -->
    <div class="usx-frontmatter-card">
      <span v-for="(val, key) in recipe.frontmatter" :key="key" class="usx-frontmatter-chip">
        <span>{{ key }}:</span>
        <strong>{{ val }}</strong>
      </span>
    </div>

    <h1>{{ recipe.title }}</h1>
    <p class="intro-paragraph">{{ recipe.intro }}</p>

    <!-- Callout Blocks -->
    <div
      v-for="callout in recipe.callouts"
      :key="callout.title"
      class="usx-callout"
      :class="[`usx-callout-${callout.type}`]"
    >
      <div class="usx-callout-header">
        <span v-if="callout.type === 'note'" class="material-symbols-outlined">info</span>
        <span v-else-if="callout.type === 'tip'" class="material-symbols-outlined">lightbulb</span>
        <span v-else-if="callout.type === 'important'" class="material-symbols-outlined">priority_high</span>
        <span v-else-if="callout.type === 'warning'" class="material-symbols-outlined">warning</span>
        <span v-else class="material-symbols-outlined">error</span>
        <span>{{ callout.title }}</span>
      </div>
      <div>{{ callout.body }}</div>
    </div>

    <!-- Structured Data Table -->
    <h2>Execution Lanes Matrix</h2>
    <table>
      <thead>
        <tr>
          <th v-for="h in recipe.tableData.headers" :key="h">{{ h }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(row, i) in recipe.tableData.rows" :key="i">
          <td v-for="(cell, j) in row" :key="j">{{ cell }}</td>
        </tr>
      </tbody>
    </table>

    <!-- Monospace Code Snippet -->
    <h2>Contract Definition</h2>
    <pre><code>{{ recipe.codeSnippet.code }}</code></pre>
  </div>
</template>

<style scoped>
@import '@udos/usx-tokens/usx-prose.css';

.prose-recipe-container {
  padding: 0.5rem 0;
  width: 100%;
}

.intro-paragraph {
  font-size: 1.05rem;
  color: var(--usx-color-on-surface-variant, #c4c6d0);
  line-height: 1.6;
}
</style>

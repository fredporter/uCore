<script setup lang="ts">
import type { TeletextRecipe } from '../recipes'

defineProps<{
  recipe: TeletextRecipe
}>()

// Helper to convert ANSI color codes to styled HTML spans
function parseAnsi(text: string): string {
  const colorMap: Record<string, string> = {
    '30': '#000000',
    '31': '#ff0000', // Red
    '32': '#00ff00', // Green
    '33': '#ffff00', // Yellow
    '34': '#0000ff', // Blue
    '35': '#ff00ff', // Magenta
    '36': '#00ffff', // Cyan
    '37': '#ffffff', // White
  }

  let html = text
  html = html.replace(/\x1b\[3([0-7])m\x1b\[1m(.*?)\x1b\[0m/g, (_, code, content) => {
    return `<span style="color:${colorMap['3' + code]}; font-weight:bold; font-size:1.15em;">${content}</span>`
  })
  html = html.replace(/\x1b\[3([0-7])m(.*?)\x1b\[0m/g, (_, code, content) => {
    return `<span style="color:${colorMap['3' + code]}">${content}</span>`
  })
  return html
}
</script>

<template>
  <div class="teletext-recipe-container">
    <div class="teletext-header-meta">
      <span class="teletext-tag">GridCore Recipe: {{ recipe.recipe }}</span>
      <span class="teletext-tag">Matrix: 40 × 25 Cell Lattice</span>
      <span class="teletext-tag">Engine: Ceefax / Mode 7</span>
    </div>

    <!-- Teletext CRT Bezel & Screen -->
    <div class="teletext-crt-frame">
      <div class="teletext-screen">
        <!-- Top Teletext Header Line -->
        <div class="teletext-top-bar">
          <span class="page-num">{{ recipe.pageNumber }}</span>
          <span class="service-name">{{ recipe.magazine }}</span>
          <span class="clock-str">100 Wed 09 Sep 17:58/44</span>
        </div>

        <!-- 24 Rows of 40 Columns Matrix -->
        <div class="teletext-grid-canvas">
          <div
            v-for="(line, idx) in recipe.lines"
            :key="idx"
            class="teletext-row"
            v-html="parseAnsi(line)"
          ></div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.teletext-recipe-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  width: 100%;
}

.teletext-header-meta {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.teletext-tag {
  font-size: 0.75rem;
  padding: 0.25rem 0.6rem;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 4px;
  color: #ffcc00;
  font-family: var(--usx-font-family-mono, monospace);
}

.teletext-crt-frame {
  padding: 1.25rem;
  background: #0a0a0c;
  border-radius: 12px;
  border: 2px solid #222;
  box-shadow: inset 0 0 20px rgba(0, 0, 0, 0.9), 0 8px 24px rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
}

.teletext-screen {
  background: #000000;
  width: 100%;
  max-width: 680px;
  padding: 1rem 1.25rem;
  font-family: 'Bedstead', 'VT323', 'Courier New', Courier, monospace;
  font-size: 1.15rem;
  line-height: 1.22;
  letter-spacing: 0.05em;
  color: #ffffff;
  border: 1px solid #1a1a1a;
  box-shadow: inset 0 0 10px rgba(0, 255, 255, 0.05);
}

.teletext-top-bar {
  display: flex;
  justify-content: space-between;
  color: #ffffff;
  background: #0000ff;
  padding: 0.15rem 0.5rem;
  margin-bottom: 0.5rem;
  font-weight: bold;
}

.teletext-grid-canvas {
  display: flex;
  flex-direction: column;
}

.teletext-row {
  white-space: pre;
  height: 1.3em;
}
</style>

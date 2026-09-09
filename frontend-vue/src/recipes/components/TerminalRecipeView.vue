<template>
  <div class="terminal-recipe-container">
    <div class="terminal-header-meta">
      <span class="term-tag">GridCore Canvas: &lt;gridui-canvas&gt;</span>
      <span class="term-tag">Matrix: 42 × 27 (40×25 Screen + Bezel Ring)</span>
      <span class="term-tag">Font: Press Start 2P (Square Cells)</span>
      <span class="term-tag">Theme: Commodore 64 (#2c4a8c Bezel)</span>
    </div>

    <!-- Authentic GridCore Viewport Container (matching /ucode terminal) -->
    <div class="ucode-viewport ucode-viewport--terminal" ref="containerRef"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import type { TerminalRecipe } from '../recipes'
import { createGridUICanvas, type GridUICanvasElement } from '../../grid-core/gridui-canvas'
import { createBuffer, writeString } from '../../grid-core/buffer'
import type { GridBuffer } from '@udos/gridcore/buffer/cell'

const props = defineProps<{
  recipe: TerminalRecipe
}>()

const containerRef = ref<HTMLDivElement>()
let canvasEl: GridUICanvasElement | null = null

function buildTerminalBuffer(): GridBuffer {
  // 42 columns x 27 rows (40x25 active terminal + 1-cell black border)
  const COLS = 42
  const ROWS = 27
  let buf = createBuffer(COLS, ROWS)

  // Top C64 BASIC Header
  buf = writeString(buf, 5, 1, '**** COMMODORE 64 BASIC V2 ****', 6, 0, true)
  buf = writeString(buf, 2, 2, '64K RAM SYSTEM  38911 BASIC BYTES FREE', 6, 0, false)
  buf = writeString(buf, 2, 4, 'READY.', 6, 0, false)
  buf = writeString(buf, 2, 5, 'RUN "UDOS-WORKBENCH"', 7, 0, true)

  // Status line from recipe
  buf = writeString(buf, 2, 7, '┌── ' + (props.recipe.statusBar.slice(0, 32) || 'UDOS SYSTEM') + ' ──┐', 3, 0, false)

  // Render split pane lines from recipe
  let currRow = 9
  if (props.recipe.splitPanes && props.recipe.splitPanes.length > 0) {
    const leftPane = props.recipe.splitPanes[0]
    const rightPane = props.recipe.splitPanes[1]

    const maxLines = Math.min(
      Math.max(leftPane?.lines?.length ?? 0, rightPane?.lines?.length ?? 0),
      14,
    )

    for (let i = 0; i < maxLines; i++) {
      if (currRow >= 23) break
      const leftText = (leftPane?.lines?.[i] ?? '').slice(0, 18).padEnd(18, ' ')
      const rightText = (rightPane?.lines?.[i] ?? '').slice(0, 19).padEnd(19, ' ')
      const combined = `│${leftText}│${rightText}│`
      buf = writeString(buf, 2, currRow, combined, 7, 0, false)
      currRow++
    }
  }

  // Bottom prompt and cursor
  buf = writeString(buf, 2, currRow < 24 ? currRow : 24, 'READY.', 6, 0, false)
  buf = writeString(buf, 2, Math.min(currRow + 1, 25), '█', 7, 0, true)

  return buf
}

function renderCanvas() {
  if (!containerRef.value) return
  if (!canvasEl) {
    canvasEl = createGridUICanvas({
      cols: 42,
      rows: 27,
      font: 'pressstart2p',
      cellSize: 18,
      squareCells: true,
    })
    canvasEl.style.flexShrink = '0'
    containerRef.value.appendChild(canvasEl)
  }
  const buf = buildTerminalBuffer()
  canvasEl.setBuffer(buf)
  nextTick(() => canvasEl?.refit())
}

onMounted(() => {
  renderCanvas()
})

onUnmounted(() => {
  if (canvasEl) {
    canvasEl.remove()
    canvasEl = null
  }
})

watch(() => props.recipe, () => {
  renderCanvas()
}, { deep: true })
</script>

<style scoped>
.terminal-recipe-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  width: 100%;
}

.terminal-header-meta {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.term-tag {
  font-size: 0.75rem;
  padding: 0.25rem 0.6rem;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 4px;
  color: #58a6ff;
  font-family: var(--usx-font-family-mono, monospace);
}

/* Authentic GridCore Terminal viewport (darker blue bezel #2c4a8c around the grid) */
.ucode-viewport--terminal {
  padding: 4%;
  background: #2c4a8c;
  min-height: 540px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--usx-radius-md);
  box-shadow: inset 0 0 20px rgba(0, 0, 0, 0.6), 0 8px 32px rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.ucode-viewport--terminal :deep(gridui-canvas) {
  flex-shrink: 0;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.8);
}
</style>

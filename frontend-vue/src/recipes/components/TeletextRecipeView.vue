<template>
  <div class="teletext-recipe-container">
    <div class="teletext-header-meta">
      <span class="teletext-tag">GridCore Canvas: &lt;gridui-canvas&gt;</span>
      <span class="teletext-tag">Matrix: 40 × 25 Mode 7</span>
      <span class="teletext-tag">Font: Bedstead (SAA5050)</span>
      <span class="teletext-tag">Palette: BBC Ceefax 8-Colour</span>
    </div>

    <!-- Authentic GridCore Viewport Container (matching /ucode?tab=teletext) -->
    <div class="ucode-viewport" ref="containerRef"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import type { TeletextRecipe } from '../recipes'
import { createGridUICanvas, type GridUICanvasElement } from '../../grid-core/gridui-canvas'
import { createBuffer, writeString } from '../../grid-core/buffer'
import type { GridBuffer } from '@udos/gridcore/buffer/cell'

const props = defineProps<{
  recipe: TeletextRecipe
}>()

const containerRef = ref<HTMLDivElement>()
let canvasEl: GridUICanvasElement | null = null

function buildTeletextBuffer(): GridBuffer {
  // 40 columns x 25 rows canonical Ceefax matrix
  let buf = createBuffer(40, 25)

  // Top header row: P100 CEEFAX 100 Wed 09 Sep 18:45/00
  buf = writeString(buf, 0, 0, 'P100  ', 3, 4, true)
  buf = writeString(buf, 6, 0, 'CEEFAX 100', 7, 4, true)
  buf = writeString(buf, 17, 0, ' Wed 09 Sep ', 3, 4, true)
  buf = writeString(buf, 30, 0, '18:45/12', 2, 4, true)

  const defaultLines = [
    '                                        ',
    ' \x1b[33m\x1b[1muDOS SYSTEM TELEMETRY INDEX\x1b[0m            ',
    ' \x1b[36m======================================\x1b[0m ',
    '                                        ',
    ' \x1b[32m101\x1b[0m \x1b[37mSYSTEM HEALTH & LOCAL RUNTIMES\x1b[0m    ',
    ' \x1b[32m102\x1b[0m \x1b[37mDEVELOPER WORKBENCH REVISIONS\x1b[0m    ',
    ' \x1b[32m103\x1b[0m \x1b[37mBUDGET & OLLAMA LOCAL INFERENCE\x1b[0m  ',
    ' \x1b[32m104\x1b[0m \x1b[37muCODE BASIC & AMOS CAPSULES\x1b[0m     ',
    '                                        ',
    ' \x1b[31m[HEADLINE]\x1b[0m                             ',
    ' \x1b[37mSPRINT 4B SURFACE SYSTEM ONLINE.\x1b[0m       ',
    ' \x1b[37mPREDICTABLE RECIPES LOCK DESIGN STYLE\x1b[0m  ',
    ' \x1b[37mACROSS ALL EXTENSIONS & CORE REPOS.\x1b[0m    ',
    '                                        ',
    ' \x1b[34m--------------------------------------\x1b[0m ',
    ' \x1b[33mSTATUS:\x1b[0m \x1b[32mALL CANONICAL REPOS SYNCED\x1b[0m     ',
    ' \x1b[33mGATE:\x1b[0m   \x1b[32mDEV READINESS ACCEPTED (10/10)\x1b[0m ',
    '                                        ',
    ' \x1b[35mSELECT PAGE NUMBER OR PRESS FASTEXT\x1b[0m    ',
  ]

  const rawLines = props.recipe.lines?.length ? props.recipe.lines : defaultLines

  const colorMap: Record<string, number> = {
    '30': 0, // black
    '31': 1, // red
    '32': 2, // green
    '33': 3, // yellow
    '34': 4, // blue
    '35': 5, // magenta
    '36': 6, // cyan
    '37': 7, // white
  }

  for (let r = 0; r < Math.min(rawLines.length, 23); r++) {
    const rawLine = rawLines[r]
    let col = 0
    let currentFg = 7
    let currentBg = 0
    let isBold = false
    let i = 0

    while (i < rawLine.length && col < 40) {
      if (rawLine[i] === '\x1b' && rawLine[i + 1] === '[') {
        const mIdx = rawLine.indexOf('m', i)
        if (mIdx !== -1) {
          const code = rawLine.slice(i + 2, mIdx)
          if (code === '0') {
            currentFg = 7
            currentBg = 0
            isBold = false
          } else if (code === '1') {
            isBold = true
          } else if (colorMap[code] !== undefined) {
            currentFg = colorMap[code]
          }
          i = mIdx + 1
          continue
        }
      }
      const char = rawLine[i]
      buf[r + 1][col] = { char, fg: currentFg, bg: currentBg, bold: isBold }
      col++
      i++
    }
  }

  // Row 24: BBC FastExt color keys
  buf = writeString(buf, 1, 24, 'INDEX', 7, 1, true)
  buf = writeString(buf, 11, 24, 'NEXT', 7, 2, true)
  buf = writeString(buf, 21, 24, 'HELP', 0, 3, true)
  buf = writeString(buf, 31, 24, 'QUIT', 7, 4, true)

  return buf
}

function renderCanvas() {
  if (!containerRef.value) return
  if (!canvasEl) {
    canvasEl = createGridUICanvas({
      cols: 40,
      rows: 25,
      font: 'bedstead',
      cellSize: 20,
      fitExact: true,
    })
    canvasEl.style.flexShrink = '0'
    containerRef.value.appendChild(canvasEl)
  }
  const buf = buildTeletextBuffer()
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

.ucode-viewport {
  flex: 1;
  min-width: 0;
  min-height: 520px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: auto;
  padding: 2%;
  background: #000000;
  border-radius: var(--usx-radius-md);
  border: 1px solid #1a1a1a;
  box-shadow: inset 0 0 24px rgba(0, 0, 0, 0.95), 0 8px 32px rgba(0, 0, 0, 0.5);
}

.ucode-viewport :deep(gridui-canvas) {
  flex-shrink: 0;
}
</style>

<script setup lang="ts">
import type { TerminalRecipe } from '../recipes'

defineProps<{
  recipe: TerminalRecipe
}>()
</script>

<template>
  <div class="terminal-recipe-container">
    <div class="terminal-header-meta">
      <span class="term-tag">GridCore Recipe: {{ recipe.recipe }}</span>
      <span class="term-tag">Matrix: {{ recipe.cols }} × {{ recipe.rows }} Monospace Grid</span>
      <span class="term-tag">Engine: VT100 / ANSI Curses</span>
    </div>

    <!-- Terminal Window Frame -->
    <div class="terminal-window">
      <div class="terminal-titlebar">
        <div class="window-buttons">
          <span class="win-btn btn-close"></span>
          <span class="win-btn btn-min"></span>
          <span class="win-btn btn-max"></span>
        </div>
        <span class="win-title">{{ recipe.statusBar }}</span>
        <span class="term-badge">ANSI</span>
      </div>

      <!-- Split Curses Screen -->
      <div class="terminal-screen-grid">
        <div
          v-for="pane in recipe.splitPanes"
          :key="pane.title"
          class="terminal-pane"
          :style="{ width: pane.width }"
        >
          <div class="pane-title">{{ pane.title }}</div>
          <div class="pane-content">
            <div
              v-for="(line, idx) in pane.lines"
              :key="idx"
              class="terminal-line"
            >
              {{ line }}
            </div>
          </div>
        </div>
      </div>

      <!-- Bottom Status Bar -->
      <div class="terminal-statusbar">
        <span>F1 Help | F2 Menu | F3 View | F5 Copy | F7 Mkdir | F8 Delete | F10 Quit</span>
        <span>READY</span>
      </div>
    </div>
  </div>
</template>

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

.terminal-window {
  border-radius: 10px;
  overflow: hidden;
  background: #0d1117;
  border: 1px solid rgba(255, 255, 255, 0.15);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.6);
  font-family: var(--usx-font-family-mono, ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace);
  width: 100%;
}

.terminal-titlebar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 0.85rem;
  background: #161b22;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  font-size: 0.75rem;
}

.window-buttons {
  display: flex;
  gap: 6px;
}

.win-btn {
  width: 11px;
  height: 11px;
  border-radius: 50%;
}
.btn-close { background: #ff5f56; }
.btn-min { background: #ffbd2e; }
.btn-max { background: #27c93f; }

.win-title {
  color: #8b949e;
  font-size: 0.75rem;
}

.term-badge {
  font-size: 0.65rem;
  padding: 0.15rem 0.4rem;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.1);
  color: #c9d1d9;
}

.terminal-screen-grid {
  display: flex;
  padding: 0.75rem;
  gap: 0.75rem;
  background: #010409;
  min-height: 280px;
}

.terminal-pane {
  display: flex;
  flex-direction: column;
}

.pane-title {
  font-size: 0.72rem;
  color: #58a6ff;
  padding-bottom: 0.35rem;
  font-weight: 600;
  letter-spacing: 0.05em;
}

.pane-content {
  font-size: 0.82rem;
  line-height: 1.35;
  color: #c9d1d9;
}

.terminal-line {
  white-space: pre;
}

.terminal-statusbar {
  display: flex;
  justify-content: space-between;
  padding: 0.35rem 0.85rem;
  background: #004d40;
  color: #ffffff;
  font-size: 0.72rem;
  font-weight: 500;
}
</style>

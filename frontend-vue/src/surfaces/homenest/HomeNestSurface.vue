<template>
  <div class="homenest-surface-wrapper">
    <header class="homenest-header">
      <div class="homenest-header__title-group">
        <h1 class="homenest-header__title">HomeNest</h1>
        <UBadge type="success" size="sm">Media & Steam Living-Room Console</UBadge>
      </div>
    </header>

    <div class="homenest-surface-body">
      <!-- Status Summary -->
      <div class="homenest-summary-grid">
        <div class="homenest-stat-card">
          <div class="homenest-stat-value text-success">{{ lifecycleState.toUpperCase() }}</div>
          <div class="homenest-stat-label">Presentation State</div>
        </div>
        <div class="homenest-stat-card">
          <div class="homenest-stat-value text-info">{{ activePresentation || 'None' }}</div>
          <div class="homenest-stat-label">Active Session</div>
        </div>
        <div class="homenest-stat-card">
          <div class="homenest-stat-value text-primary">{{ queue.length }}</div>
          <div class="homenest-stat-label">Queued Media</div>
        </div>
        <div class="homenest-stat-card">
          <div class="homenest-stat-value text-warning">{{ focusTarget }}</div>
          <div class="homenest-stat-label">Input Focus</div>
        </div>
      </div>

      <!-- Controls & Launcher Card -->
      <div class="homenest-card">
        <div class="homenest-card-header">
          <h2>Presentation Lifecycle Controls</h2>
          <UBadge :type="running ? 'success' : 'neutral'" size="sm">{{ running ? 'LIVE' : 'IDLE' }}</UBadge>
        </div>
        <div class="homenest-card-content flex gap-3 p-4">
          <button
            class="usx-btn usx-btn--primary"
            :disabled="running && activePresentation === 'steam-console'"
            @click="startPresentation('steam-console')"
          >
            <UIcon name="sports_esports" />
            <span>Launch Steam Console</span>
          </button>
          <button
            class="usx-btn usx-btn--secondary"
            :disabled="running && activePresentation === 'thin-gui'"
            @click="startPresentation('thin-gui')"
          >
            <UIcon name="tv" />
            <span>Launch Thin GUI</span>
          </button>
          <button
            class="usx-btn usx-btn--danger"
            :disabled="!running"
            @click="stopPresentation"
          >
            <UIcon name="stop" />
            <span>Stop Session & Restore Focus</span>
          </button>
        </div>
      </div>

      <!-- Playback Queue Card -->
      <div class="homenest-card">
        <div class="homenest-card-header">
          <h2>Playback Handoff Queue</h2>
          <button class="usx-btn usx-btn--sm usx-btn--secondary" @click="addSampleMedia">
            <UIcon name="add" />
            <span>Enqueue Sample Media</span>
          </button>
        </div>
        <div class="homenest-event-list">
          <div v-if="queue.length === 0" class="p-4 text-xs text-zinc-500 text-center font-mono">
            No media currently queued.
          </div>
          <div v-for="(item, i) in queue" :key="i" class="homenest-event-row">
            <span class="homenest-event-time font-mono">{{ item.queued_at?.slice(11, 19) || '12:00:00' }}</span>
            <UBadge type="info" size="sm">{{ item.status || 'queued' }}</UBadge>
            <span class="homenest-event-msg font-medium">{{ item.item_id }}</span>
            <span class="text-xs text-zinc-400 font-mono">Target: {{ item.target_client }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import UIcon from '../../skills/atoms/UIcon.vue'
import UBadge from '../../skills/atoms/UBadge.vue'

const lifecycleState = ref('idle')
const activePresentation = ref<string | null>(null)
const running = ref(false)
const focusTarget = ref('console')

const queue = ref<any[]>([
  {
    item_id: 'film-interstellar-4k',
    status: 'queued',
    target_client: 'living-room-tv',
    queued_at: new Date().toISOString(),
  },
])

function startPresentation(type: string) {
  activePresentation.value = type
  lifecycleState.value = 'running'
  running.value = true
  focusTarget.value = type
}

function stopPresentation() {
  activePresentation.value = null
  lifecycleState.value = 'idle'
  running.value = false
  focusTarget.value = 'console'
}

function addSampleMedia() {
  queue.value.push({
    item_id: `media-sample-${Math.floor(Math.random() * 1000)}`,
    status: 'queued',
    target_client: 'living-room-tv',
    queued_at: new Date().toISOString(),
  })
}
</script>

<style scoped>
.homenest-surface-wrapper {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--usx-color-surface-base, var(--usx-color-bg, #0d0e11));
  color: var(--usx-color-on-surface, #e2e4e9);
  padding: var(--usx-spacing-md);
  gap: var(--usx-spacing-md);
  max-width: var(--usx-max-width);
  margin: 0 auto;
  width: 100%;
}
.homenest-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: var(--usx-spacing-sm);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
}
.homenest-header__title-group {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
}
.homenest-header__title {
  font-size: var(--usx-font-size-xl);
  font-weight: 600;
  margin: 0;
  color: var(--usx-color-on-surface);
}
.homenest-surface-body {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-md);
}
.homenest-summary-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--usx-spacing-sm);
}
.homenest-stat-card {
  background: var(--usx-color-surface);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
}
.homenest-stat-value {
  font-size: var(--usx-font-size-xl);
  font-weight: 700;
  font-family: monospace;
}
.text-success {
  color: var(--usx-color-success);
}
.text-info {
  color: var(--usx-color-info);
}
.text-primary {
  color: var(--usx-color-primary);
}
.text-warning {
  color: var(--usx-color-warning);
}
.homenest-stat-label {
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
}
.homenest-card {
  background: var(--usx-color-surface);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  overflow: hidden;
}
.homenest-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
}
.homenest-card-header h2 {
  font-size: var(--usx-font-size-sm);
  font-weight: 600;
  margin: 0;
}
.homenest-event-list {
  display: flex;
  flex-direction: column;
}
.homenest-event-row {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
  font-size: var(--usx-font-size-sm);
}
.homenest-event-time {
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-xs);
}
</style>

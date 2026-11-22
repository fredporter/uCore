<template>
  <div class="homenest-surface-wrapper">
    <header class="homenest-header">
      <div class="homenest-header__title-group">
        <h1 class="homenest-header__title">HomeNook</h1>
        <p>Media and Steam living-room console</p>
      </div>
    </header>

    <div class="homenest-surface-body">
      <!-- Status Summary -->
      <div class="homenest-summary-grid">
        <div class="homenest-stat-card">
          <div class="homenest-stat-value">{{ lifecycleState.toUpperCase() }}</div>
          <div class="homenest-stat-label">Presentation State</div>
        </div>
        <div class="homenest-stat-card">
          <div class="homenest-stat-value">{{ activePresentation || 'None' }}</div>
          <div class="homenest-stat-label">Active Session</div>
        </div>
        <div class="homenest-stat-card">
          <div class="homenest-stat-value">{{ queue.length }}</div>
          <div class="homenest-stat-label">Queued Media</div>
        </div>
        <div class="homenest-stat-card">
          <div class="homenest-stat-value">{{ focusTarget }}</div>
          <div class="homenest-stat-label">Input Focus</div>
        </div>
      </div>

      <!-- Controls & Launcher Card -->
      <div class="homenest-card">
        <div class="homenest-card-header">
          <h2>Presentation Lifecycle Controls</h2>
          <UBadge :type="running ? 'success' : 'neutral'" size="sm">{{ running ? 'LIVE' : 'IDLE' }}</UBadge>
        </div>
        <div class="homenest-card-content">
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
          <div v-if="queue.length === 0" class="homenest-empty">
            No media currently queued.
          </div>
          <div v-for="(item, i) in queue" :key="i" class="homenest-event-row">
            <span class="homenest-event-time">{{ item.queued_at?.slice(11, 19) || '12:00:00' }}</span>
            <UBadge type="info" size="sm">{{ item.status || 'queued' }}</UBadge>
            <span class="homenest-event-msg">{{ item.item_id }}</span>
            <span class="homenest-event-target">Target: {{ item.target_client }}</span>
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
  min-width: 0;
  overflow: auto;
  background: var(--usx-color-background);
  color: var(--usx-color-on-surface);
  font-family: var(--usx-font-family-sans);
}

.homenest-header {
  padding: var(--usx-spacing-md);
  border-block-end: var(--usx-border-width) solid var(--usx-color-border);
}

.homenest-header__title-group,
.homenest-stat-card {
  display: grid;
  gap: var(--usx-spacing-xs);
}

.homenest-header__title,
.homenest-header p,
.homenest-card-header h2 {
  margin: 0;
}

.homenest-header__title,
.homenest-stat-value {
  font-size: var(--usx-font-size-xl);
  font-weight: var(--usx-font-weight-semibold);
}

.homenest-header p,
.homenest-stat-label,
.homenest-event-time,
.homenest-event-target,
.homenest-empty {
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
}

.homenest-surface-body,
.homenest-summary-grid,
.homenest-card {
  display: grid;
  gap: var(--usx-spacing-md);
  min-width: 0;
}

.homenest-surface-body { padding: var(--usx-spacing-md); }

.homenest-summary-grid {
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 10rem), 1fr));
}

.homenest-stat-card,
.homenest-card {
  padding: var(--usx-spacing-md);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: var(--usx-color-surface);
  overflow-wrap: anywhere;
}

.homenest-stat-value {
  font-variant-numeric: tabular-nums;
}

.homenest-card-header,
.homenest-card-content {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--usx-spacing-sm);
}

.homenest-card-header { justify-content: space-between; }

.homenest-card-header h2 {
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-semibold);
}

.homenest-card .usx-btn {
  min-block-size: var(--usx-touch-min);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border-radius: var(--usx-radius-sm);
  font-size: var(--usx-font-size-sm);
  line-height: var(--usx-line-height-tight);
  box-shadow: none;
}

.homenest-card .usx-btn--primary:hover:not(:disabled) {
  color: var(--usx-color-on-primary);
}

.homenest-card .usx-btn--danger:not(:disabled) {
  border-color: var(--usx-color-danger);
  color: var(--usx-color-danger);
  background: var(--usx-color-surface);
}

.homenest-card .usx-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.homenest-card .usx-btn:focus-visible {
  outline: 2px solid var(--usx-color-primary);
  outline-offset: 2px;
}

.homenest-event-row {
  display: grid;
  grid-template-columns: max-content max-content minmax(0, 1fr) minmax(0, 11rem);
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding-block: var(--usx-spacing-sm);
  border-block-start: var(--usx-border-width) solid var(--usx-color-border);
  font-size: var(--usx-font-size-sm);
}

.homenest-event-time { font-variant-numeric: tabular-nums; }

@media (max-width: 720px) {
  .homenest-event-row {
    grid-template-columns: minmax(0, 1fr) auto;
  }

  .homenest-event-msg,
  .homenest-event-target {
    grid-column: 1 / -1;
  }
}
</style>

<template>
  <div class="homenest-surface-wrapper">
    <div class="homenest-surface-toolbar">
      <button
        class="homenest-surface-back"
        @click="router.push('/')"
        title="Back to Dashboard"
      >
        ← Dashboard
      </button>
      <span class="homenest-surface-label">HomeNest</span>
      <span class="homenest-surface-badge">Media & Steam Living-Room Console</span>
    </div>

    <div class="homenest-surface-body">
      <!-- Status Summary -->
      <div class="homenest-summary-grid">
        <div class="homenest-stat-card">
          <div class="homenest-stat-value text-emerald-400">{{ lifecycleState.toUpperCase() }}</div>
          <div class="homenest-stat-label">Presentation State</div>
        </div>
        <div class="homenest-stat-card">
          <div class="homenest-stat-value text-sky-400">{{ activePresentation || 'None' }}</div>
          <div class="homenest-stat-label">Active Session</div>
        </div>
        <div class="homenest-stat-card">
          <div class="homenest-stat-value text-purple-400">{{ queue.length }}</div>
          <div class="homenest-stat-label">Queued Media</div>
        </div>
        <div class="homenest-stat-card">
          <div class="homenest-stat-value text-amber-400">{{ focusTarget }}</div>
          <div class="homenest-stat-label">Input Focus</div>
        </div>
      </div>

      <!-- Controls & Launcher Card -->
      <div class="homenest-card">
        <div class="homenest-card-header">
          <h2>Presentation Lifecycle Controls</h2>
          <span class="homenest-badge font-mono">{{ running ? 'LIVE' : 'IDLE' }}</span>
        </div>
        <div class="homenest-card-content flex gap-3 p-4">
          <button
            class="homenest-btn homenest-btn--primary"
            :disabled="running && activePresentation === 'steam-console'"
            @click="startPresentation('steam-console')"
          >
            🎮 Launch Steam Console
          </button>
          <button
            class="homenest-btn homenest-btn--secondary"
            :disabled="running && activePresentation === 'thin-gui'"
            @click="startPresentation('thin-gui')"
          >
            📺 Launch Thin GUI
          </button>
          <button
            class="homenest-btn homenest-btn--danger"
            :disabled="!running"
            @click="stopPresentation"
          >
            ⏹ Stop Session & Restore Focus
          </button>
        </div>
      </div>

      <!-- Playback Queue Card -->
      <div class="homenest-card">
        <div class="homenest-card-header">
          <h2>Playback Handoff Queue</h2>
          <button class="homenest-btn" @click="addSampleMedia">Enqueue Sample Media</button>
        </div>
        <div class="homenest-event-list">
          <div v-if="queue.length === 0" class="p-4 text-xs text-zinc-500 text-center font-mono">
            No media currently queued.
          </div>
          <div v-for="(item, i) in queue" :key="i" class="homenest-event-row">
            <span class="homenest-event-time">{{ item.queued_at?.slice(11, 19) || '12:00:00' }}</span>
            <span class="homenest-badge homenest-badge--info">{{ item.status || 'queued' }}</span>
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
import { useRouter } from 'vue-router'

const router = useRouter()

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
  background: var(--usx-color-bg, #0d0e11);
  color: var(--usx-color-text, #e2e4e9);
  padding: 1rem;
  gap: 1rem;
}
.homenest-surface-toolbar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--usx-color-border, #262930);
}
.homenest-surface-back {
  background: transparent;
  border: 1px solid var(--usx-color-border, #262930);
  color: var(--usx-color-text, #e2e4e9);
  padding: 0.35rem 0.75rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.8rem;
}
.homenest-surface-label {
  font-weight: 600;
  font-size: 1.1rem;
}
.homenest-surface-badge {
  font-size: 0.75rem;
  padding: 0.2rem 0.5rem;
  border-radius: 9999px;
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
  font-family: monospace;
}
.homenest-surface-body {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.homenest-summary-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.75rem;
}
.homenest-stat-card {
  background: var(--usx-color-surface, #16181d);
  border: 1px solid var(--usx-color-border, #262930);
  border-radius: 8px;
  padding: 0.75rem;
}
.homenest-stat-value {
  font-size: 1.25rem;
  font-weight: 700;
  font-family: monospace;
}
.homenest-stat-label {
  font-size: 0.75rem;
  color: var(--usx-color-text-muted, #8b92a5);
}
.homenest-card {
  background: var(--usx-color-surface, #16181d);
  border: 1px solid var(--usx-color-border, #262930);
  border-radius: 8px;
  overflow: hidden;
}
.homenest-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--usx-color-border, #262930);
}
.homenest-card-header h2 {
  font-size: 0.95rem;
  font-weight: 600;
  margin: 0;
}
.homenest-btn {
  background: var(--usx-color-surface-hover, #20242c);
  border: 1px solid var(--usx-color-border, #262930);
  color: var(--usx-color-text, #e2e4e9);
  padding: 0.4rem 0.8rem;
  border-radius: 6px;
  font-size: 0.8rem;
  cursor: pointer;
}
.homenest-btn--primary {
  background: #2563eb;
  color: #fff;
  border-color: #3b82f6;
}
.homenest-btn--secondary {
  background: #059669;
  color: #fff;
  border-color: #10b981;
}
.homenest-btn--danger {
  background: #dc2626;
  color: #fff;
  border-color: #ef4444;
}
.homenest-event-list {
  display: flex;
  flex-direction: column;
}
.homenest-event-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.6rem 1rem;
  border-bottom: 1px solid var(--usx-color-border, #262930);
  font-size: 0.8rem;
}
.homenest-event-time {
  font-family: monospace;
  color: var(--usx-color-text-muted, #8b92a5);
  font-size: 0.75rem;
}
.homenest-badge {
  font-size: 0.7rem;
  padding: 0.15rem 0.4rem;
  border-radius: 4px;
}
.homenest-badge--info {
  background: rgba(59, 130, 246, 0.15);
  color: #60a5fa;
}
</style>

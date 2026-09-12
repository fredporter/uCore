<template>
  <div class="ha-surface-wrapper">
    <div class="ha-surface-toolbar">
      <button
        class="ha-surface-back"
        @click="router.push('/')"
        title="Back to Dashboard"
      >
        ← Dashboard
      </button>
      <span class="ha-surface-label">Home Assistant</span>
      <span class="ha-surface-badge">Matter & Local Control Surface</span>
    </div>

    <div class="ha-surface-body">
      <!-- Status Summary Cards -->
      <div class="ha-summary-grid">
        <div class="ha-stat-card">
          <div class="ha-stat-value" :class="connectionStatusColor">{{ connectionStatus.toUpperCase() }}</div>
          <div class="ha-stat-label">HA Bridge Status</div>
        </div>
        <div class="ha-stat-card">
          <div class="ha-stat-value text-emerald-400">ONLINE</div>
          <div class="ha-stat-label">Matter Gateway</div>
        </div>
        <div class="ha-stat-card">
          <div class="ha-stat-value text-sky-400">{{ entities.length }}</div>
          <div class="ha-stat-label">Allowlisted Entities</div>
        </div>
        <div class="ha-stat-card">
          <div class="ha-stat-value text-purple-400">{{ recentEvents.length }}</div>
          <div class="ha-stat-label">Service Invocations</div>
        </div>
      </div>

      <!-- Quick Scenes -->
      <div class="ha-card">
        <div class="ha-card-header">
          <h2>Quick Scene Execution</h2>
          <span class="ha-badge ha-badge--info">uFlow Movie Night Ready</span>
        </div>
        <div class="ha-card-content flex flex-wrap gap-3 p-4">
          <button
            class="ha-btn ha-btn--primary"
            :disabled="isExecuting"
            @click="activateScene('scene.movie_night')"
          >
            🎬 Scene: Movie Night
          </button>
          <button
            class="ha-btn ha-btn--secondary"
            :disabled="isExecuting"
            @click="activateScene('scene.relax')"
          >
            🕯️ Scene: Relax
          </button>
          <button
            class="ha-btn ha-btn--secondary"
            :disabled="isExecuting"
            @click="activateScene('scene.reading')"
          >
            📖 Scene: Reading
          </button>
          <button
            class="ha-btn ha-btn--danger"
            :disabled="isExecuting"
            @click="activateScene('scene.all_off')"
          >
            🌙 Turn All Off
          </button>
        </div>
      </div>

      <!-- Allowlisted Entity Controls -->
      <div class="ha-card">
        <div class="ha-card-header">
          <h2>Observed Entities (Allowlisted)</h2>
          <span class="ha-badge font-mono text-xs">Strict Zero-Trust Boundary</span>
        </div>
        <div class="ha-entity-list">
          <div
            v-for="entity in entities"
            :key="entity.entity_id"
            class="ha-entity-row"
          >
            <div class="ha-entity-info">
              <span class="ha-entity-id font-mono">{{ entity.entity_id }}</span>
              <span class="ha-entity-name text-zinc-400">{{ entity.name }}</span>
            </div>
            <div class="ha-entity-state">
              <span
                class="ha-badge"
                :class="entity.state === 'on' || entity.state === 'playing' ? 'ha-badge--success' : 'ha-badge--muted'"
              >
                {{ entity.state.toUpperCase() }}
              </span>
            </div>
            <div class="ha-entity-actions">
              <button
                class="ha-btn text-xs"
                @click="toggleEntity(entity)"
              >
                {{ entity.state === 'on' ? 'Turn Off' : 'Turn On' }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Audit Log -->
      <div class="ha-card">
        <div class="ha-card-header">
          <h2>Command Audit Trail</h2>
          <button class="ha-btn text-xs" @click="clearAuditLog">Clear Log</button>
        </div>
        <div class="ha-event-list">
          <div v-if="recentEvents.length === 0" class="p-4 text-xs text-zinc-500 text-center font-mono">
            No service calls executed yet.
          </div>
          <div
            v-for="(ev, idx) in recentEvents"
            :key="idx"
            class="ha-event-row"
          >
            <span class="ha-event-time">{{ ev.timestamp }}</span>
            <span
              class="ha-badge"
              :class="ev.status === 'confirmed' ? 'ha-badge--success' : 'ha-badge--info'"
            >
              {{ ev.status.toUpperCase() }}
            </span>
            <span class="ha-event-msg font-mono text-xs">{{ ev.service }} -> {{ ev.target }}</span>
            <span class="text-xs text-zinc-400 font-mono ml-auto">{{ ev.elapsed_ms }}ms</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const connectionStatus = ref<'connected' | 'connecting' | 'disconnected'>('connected')
const isExecuting = ref(false)

const connectionStatusColor = computed(() => {
  switch (connectionStatus.value) {
    case 'connected':
      return 'text-emerald-400'
    case 'connecting':
      return 'text-amber-400'
    default:
      return 'text-red-400'
  }
})

interface Entity {
  entity_id: string
  name: string
  state: string
  domain: string
}

const entities = ref<Entity[]>([
  { entity_id: 'light.living_room_ceiling', name: 'Living Room Ceiling', state: 'on', domain: 'light' },
  { entity_id: 'light.reading_lamp', name: 'Reading Lamp', state: 'off', domain: 'light' },
  { entity_id: 'switch.soundbar', name: 'Living Room Soundbar', state: 'on', domain: 'switch' },
  { entity_id: 'media_player.living_room_tv', name: 'Living Room Smart TV', state: 'playing', domain: 'media_player' },
  { entity_id: 'scene.movie_night', name: 'Movie Night Scene', state: 'scening', domain: 'scene' },
])

interface AuditEvent {
  timestamp: string
  service: string
  target: string
  status: string
  elapsed_ms: number
}

const recentEvents = ref<AuditEvent[]>([
  {
    timestamp: '19:42:01',
    service: 'scene.turn_on',
    target: 'scene.movie_night',
    status: 'confirmed',
    elapsed_ms: 12.4,
  },
  {
    timestamp: '19:42:02',
    service: 'media_player.media_play',
    target: 'media_player.living_room_tv',
    status: 'confirmed',
    elapsed_ms: 8.1,
  },
])

function toggleEntity(entity: Entity) {
  const nextState = entity.state === 'on' ? 'off' : 'on'
  entity.state = nextState
  recentEvents.value.unshift({
    timestamp: new Date().toTimeString().slice(0, 8),
    service: `${entity.domain}.turn_${nextState}`,
    target: entity.entity_id,
    status: 'confirmed',
    elapsed_ms: Math.floor(Math.random() * 15 + 5),
  })
}

function activateScene(sceneId: string) {
  isExecuting.value = true
  setTimeout(() => {
    isExecuting.value = false
    recentEvents.value.unshift({
      timestamp: new Date().toTimeString().slice(0, 8),
      service: 'scene.turn_on',
      target: sceneId,
      status: 'confirmed',
      elapsed_ms: 14.2,
    })
    if (sceneId === 'scene.movie_night') {
      const ceiling = entities.value.find((e) => e.entity_id === 'light.living_room_ceiling')
      if (ceiling) ceiling.state = 'off'
      const lamp = entities.value.find((e) => e.entity_id === 'light.reading_lamp')
      if (lamp) lamp.state = 'off'
    } else if (sceneId === 'scene.all_off') {
      entities.value.forEach((e) => {
        if (e.domain === 'light' || e.domain === 'switch') e.state = 'off'
      })
    }
  }, 250)
}

function clearAuditLog() {
  recentEvents.value = []
}
</script>

<style scoped>
.ha-surface-wrapper {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  max-width: 1200px;
  margin: 0 auto;
}
.ha-surface-toolbar {
  display: flex;
  align-items: center;
  gap: 1rem;
}
.ha-surface-back {
  background: var(--usx-color-surface, #16181d);
  border: 1px solid var(--usx-color-border, #262930);
  color: var(--usx-color-text, #e2e4e9);
  padding: 0.35rem 0.75rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
}
.ha-surface-label {
  font-weight: 700;
  font-size: 1.25rem;
}
.ha-surface-badge {
  font-size: 0.75rem;
  padding: 0.2rem 0.5rem;
  background: rgba(59, 130, 246, 0.15);
  color: #60a5fa;
  border-radius: 9999px;
  border: 1px solid rgba(59, 130, 246, 0.3);
}
.ha-surface-body {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.ha-summary-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.75rem;
}
.ha-stat-card {
  background: var(--usx-color-surface, #16181d);
  border: 1px solid var(--usx-color-border, #262930);
  border-radius: 8px;
  padding: 0.75rem;
}
.ha-stat-value {
  font-size: 1.25rem;
  font-weight: 700;
  font-family: monospace;
}
.ha-stat-label {
  font-size: 0.75rem;
  color: var(--usx-color-text-muted, #8b92a5);
}
.ha-card {
  background: var(--usx-color-surface, #16181d);
  border: 1px solid var(--usx-color-border, #262930);
  border-radius: 8px;
  overflow: hidden;
}
.ha-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--usx-color-border, #262930);
}
.ha-card-header h2 {
  font-size: 0.95rem;
  font-weight: 600;
  margin: 0;
}
.ha-btn {
  background: var(--usx-color-surface-hover, #20242c);
  border: 1px solid var(--usx-color-border, #262930);
  color: var(--usx-color-text, #e2e4e9);
  padding: 0.4rem 0.8rem;
  border-radius: 6px;
  font-size: 0.8rem;
  cursor: pointer;
}
.ha-btn:hover {
  background: var(--usx-color-border, #262930);
}
.ha-btn--primary {
  background: #2563eb;
  color: #fff;
  border-color: #3b82f6;
}
.ha-btn--primary:hover {
  background: #1d4ed8;
}
.ha-btn--secondary {
  background: #059669;
  color: #fff;
  border-color: #10b981;
}
.ha-btn--secondary:hover {
  background: #047857;
}
.ha-btn--danger {
  background: #dc2626;
  color: #fff;
  border-color: #ef4444;
}
.ha-btn--danger:hover {
  background: #b91c1c;
}
.ha-badge {
  font-size: 0.7rem;
  padding: 0.15rem 0.4rem;
  border-radius: 4px;
}
.ha-badge--info {
  background: rgba(59, 130, 246, 0.15);
  color: #60a5fa;
}
.ha-badge--success {
  background: rgba(16, 185, 129, 0.15);
  color: #34d399;
}
.ha-badge--muted {
  background: rgba(107, 114, 128, 0.15);
  color: #9ca3af;
}
.ha-entity-list {
  display: flex;
  flex-direction: column;
}
.ha-entity-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.6rem 1rem;
  border-bottom: 1px solid var(--usx-color-border, #262930);
  font-size: 0.8rem;
}
.ha-entity-info {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}
.ha-entity-id {
  font-size: 0.8rem;
  color: var(--usx-color-text, #e2e4e9);
}
.ha-entity-name {
  font-size: 0.7rem;
}
.ha-event-list {
  display: flex;
  flex-direction: column;
}
.ha-event-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.6rem 1rem;
  border-bottom: 1px solid var(--usx-color-border, #262930);
  font-size: 0.8rem;
}
.ha-event-time {
  font-family: monospace;
  color: var(--usx-color-text-muted, #8b92a5);
  font-size: 0.75rem;
}
</style>

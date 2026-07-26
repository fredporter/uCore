<template>
  <div class="tools-panel">
    <h2 class="tools-title">Developer Tools</h2>
    <p class="tools-subtitle">Local CLI tools available on this machine.</p>

    <div v-if="loading" class="tools-loading">Checking tools...</div>
    <div v-else class="tools-grid">
      <div v-for="tool in tools" :key="tool.id" class="tools-card">
        <div class="tools-card-header">
          <UIcon :name="tool.icon || 'build'" class="tools-card-icon" />
          <div class="tools-card-info">
            <span class="tools-card-name">{{ tool.name }}</span>
            <span class="tools-card-desc">{{ tool.description }}</span>
          </div>
        </div>
        <div class="tools-card-meta">
          <UBadge :type="tool.installed ? 'success' : 'error'" size="sm">
            {{ tool.installed ? 'installed' : 'missing' }}
          </UBadge>
          <span v-if="tool.version" class="tools-card-version">{{ tool.version }}</span>
          <UBadge v-if="tool.installed" :type="tool.running ? 'success' : 'neutral'" size="sm">
            {{ tool.running ? 'running' : 'idle' }}
          </UBadge>
        </div>
      </div>
    </div>
    <p v-if="!loading && tools.length === 0" class="tools-empty">No tools detected. Ensure CLI tools are installed and in your PATH.</p>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import UIcon from '../../../skills/atoms/UIcon.vue'
import UBadge from '../../../skills/atoms/UBadge.vue'

const API_BASE = import.meta.env.VITE_SNACKBAR_URL || 'http://localhost:8484'

interface ToolInfo {
  id: string
  name: string
  description: string
  icon: string
  installed: boolean
  version: string
  running: boolean
}

const tools = ref<ToolInfo[]>([])
const loading = ref(true)

const ICON_MAP: Record<string, string> = {
  git: 'git',
  docker: 'docker',
  node: 'node',
  python: 'python',
  ollama: 'ollama',
  vscode: 'vscode',
  'github-cli': 'github',
}

async function fetchTools() {
  loading.value = true
  try {
    const res = await fetch(`${API_BASE}/api/tools`, { signal: AbortSignal.timeout(5000) })
    if (res.ok) {
      const data = await res.json()
      const list = data.tools || []
      tools.value = list.map((t: any) => ({
        id: t.id || '',
        name: t.name || t.id || 'unknown',
        description: t.description || '',
        icon: ICON_MAP[t.id] || 'build',
        installed: t.installed ?? false,
        version: t.version || '',
        running: t.running ?? false,
      }))
    }
  } catch {
    // keep empty
  }
  loading.value = false
}

onMounted(() => { fetchTools() })
</script>

<style scoped>
.tools-panel { }
.tools-title { font-size: var(--usx-font-size-xl); font-weight: var(--usx-font-weight-semibold); margin: 0 0 var(--usx-spacing-xs); }
.tools-subtitle { font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); margin: 0 0 var(--usx-spacing-lg); }
.tools-loading { text-align: center; padding: var(--usx-spacing-xl); color: var(--usx-color-on-surface-muted); font-size: var(--usx-font-size-sm); }
.tools-empty { text-align: center; padding: var(--usx-spacing-xl); color: var(--usx-color-on-surface-muted); font-size: var(--usx-font-size-sm); }
.tools-grid { display: flex; flex-direction: column; gap: var(--usx-spacing-sm); }
.tools-card { display: flex; align-items: center; justify-content: space-between; padding: var(--usx-spacing-md); background: var(--usx-color-surface); border-radius: var(--usx-radius-md); border: 1px solid var(--usx-color-border); }
.tools-card-header { display: flex; align-items: center; gap: var(--usx-spacing-sm); flex: 1; min-width: 0; }
.tools-card-icon { font-size: var(--usx-font-size-xl); flex-shrink: 0; }
.tools-card-info { display: flex; flex-direction: column; gap: var(--usx-spacing-xs); min-width: 0; }
.tools-card-name { font-size: var(--usx-font-size-base); font-weight: var(--usx-font-weight-medium); }
.tools-card-desc { font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); }
.tools-card-meta { display: flex; align-items: center; gap: var(--usx-spacing-sm); flex-shrink: 0; }
.tools-card-version { font-family: var(--usx-font-family-mono); font-size: var(--usx-font-size-xs); color: var(--usx-color-on-surface-muted); background: var(--usx-color-background); padding: var(--usx-spacing-xs) var(--usx-spacing-sm); border-radius: var(--usx-radius-sm); }
</style>
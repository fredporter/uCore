/**
 * @module stores/devMode
 * @description Dev Mode — 3-state toggle (OFF / MINIMAL / ON).
 * Probes /api/dev-layer/state directly — no separate health check needed.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export type DevModeState = 'off' | 'minimal' | 'on'

import { SNACKBAR_BASE } from '@/api/base'

const API = SNACKBAR_BASE

export const useDevModeStore = defineStore('devMode', () => {
  const mode = ref<DevModeState>('off')
  const loading = ref(true)
  const serverConfirmed = ref(false)
  const backendConnected = ref(false)

  /** Fetch mode from backend. Falls back to localStorage only as preference when offline. */
  async function probe(): Promise<void> {
    loading.value = true
    try {
      const res = await fetch(`${API}/api/dev-layer/state`, { signal: AbortSignal.timeout(1500) })
      if (res.ok) {
        const data = await res.json()
        if (data?.mode) {
          mode.value = data.mode as DevModeState
          serverConfirmed.value = true
          backendConnected.value = true
          localStorage.setItem('ucore-dev-mode', data.mode)
          loading.value = false
          return
        }
      }
    } catch {
      serverConfirmed.value = false
      backendConnected.value = false
    }
    // Fallback: check localStorage for local preference, unconfirmed
    const saved = localStorage.getItem('ucore-dev-mode')
    if (saved === 'on' || saved === 'minimal' || saved === 'off') {
      mode.value = saved as DevModeState
    }
    serverConfirmed.value = false
    loading.value = false
  }

  async function setMode(m: DevModeState): Promise<void> {
    const previous = mode.value
    mode.value = m
    try {
      const res = await fetch(`${API}/api/dev-layer/state`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: m }),
        signal: AbortSignal.timeout(1500),
      })
      if (res.ok) {
        serverConfirmed.value = true
        backendConnected.value = true
        localStorage.setItem('ucore-dev-mode', m)
      } else {
        // Rollback on server rejection
        mode.value = previous
        serverConfirmed.value = false
      }
    } catch {
      // Offline: roll back to previous mode or mark unconfirmed
      mode.value = previous
      serverConfirmed.value = false
      backendConnected.value = false
    }
  }

  async function toggle(): Promise<void> {
    loading.value = true
    try {
      const res = await fetch(`${API}/api/dev-layer/toggle`, { method: 'POST', signal: AbortSignal.timeout(2000) })
      if (res.ok) {
        const data = await res.json()
        if (data?.mode) {
          mode.value = data.mode as DevModeState
          serverConfirmed.value = true
          backendConnected.value = true
          localStorage.setItem('ucore-dev-mode', data.mode)
        }
      } else {
        serverConfirmed.value = false
      }
    } catch {
      serverConfirmed.value = false
      backendConnected.value = false
    } finally {
      loading.value = false
    }
  }

  const showDevContent = computed(() => mode.value === 'on' && serverConfirmed.value && backendConnected.value)
  const isOffline = computed(() => !backendConnected.value)
  const isConfirmedOn = computed(() => mode.value === 'on' && serverConfirmed.value && backendConnected.value)

  return {
    mode,
    loading,
    serverConfirmed,
    backendConnected,
    isConfirmedOn,
    probe,
    setMode,
    toggle,
    showDevContent,
    isOffline,
  }
})

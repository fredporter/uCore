<template>
  <div class="system-page">
    <div class="system-page-header">
      <UIcon :name="pageMeta.icon || 'dashboard'" class="system-page-header-icon" />
      <h2 class="system-page-title">{{ pageMeta.title || pageCode }}</h2>
      <UBadge type="neutral" size="sm">{{ pageCode }}</UBadge>
    </div>

    <div v-if="pageMeta" class="system-page-body">
      <p class="system-page-note">{{ pageMeta.description || 'System page content renders here.' }}</p>

      <!-- S-Page specific content -->
      <div v-if="pageCode.startsWith('S')" class="system-s-page-content">
        <div class="system-page-placeholder">
          <UIcon name="construction" class="system-page-placeholder-icon" />
          <p>S-page content module coming in Wave 2. This page ({{ pageCode }}) will host {{ pageMeta.title }}.</p>
        </div>
      </div>

      <!-- P-Page specific content -->
      <div v-else-if="pageCode.startsWith('P')" class="system-p-page-content">
        <div class="system-page-placeholder">
          <UIcon name="analytics" class="system-page-placeholder-icon" />
          <p>P-page (System Admin Panel). Data for {{ pageMeta.title }} will be fetched from backend APIs.</p>
        </div>
      </div>
    </div>

    <div v-else class="system-page-body">
      <p class="system-page-note">Unknown page: {{ pageCode }}. Not found in S-pages or P-pages registry.</p>
      <router-link to="/system?tab=pages" class="system-page-back-link">← Back to Pages Browser</router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import UIcon from '../../skills/atoms/UIcon.vue'
import UBadge from '../../skills/atoms/UBadge.vue'

const API_BASE = import.meta.env.VITE_SNACKBAR_URL || 'http://localhost:8484'
const route = useRoute()

// e.g. /system/s100 → S100
const pageCode = computed(() => {
  const raw = route.path.replace('/system/', '').replace(/\/$/, '')
  return raw.toUpperCase() || 'UNKNOWN'
})

interface PageMeta { id: string; title: string; icon: string; description?: string }
const pageMeta = ref<PageMeta | null>(null)

async function fetchPageMeta() {
  try {
    const res = await fetch(`${API_BASE}/api/system/pages`, { signal: AbortSignal.timeout(3000) })
    if (res.ok) {
      const data = await res.json()
      const pages: PageMeta[] = data.pages || []
      const found = pages.find(p => p.id.toUpperCase() === pageCode.value)
      if (found) {
        pageMeta.value = {
          ...found,
          description: found.description || `${found.id} — ${found.title} system page.`,
        }
      }
    }
  } catch {}
}

onMounted(() => { fetchPageMeta() })
</script>

<style scoped>
.system-page { padding: var(--usx-spacing-xl); max-width: 900px; }
.system-page-header { display: flex; align-items: center; gap: var(--usx-spacing-md); margin-bottom: var(--usx-spacing-lg); }
.system-page-header-icon { font-size: var(--usx-font-size-2xl); }
.system-page-title { margin: 0; font-size: var(--usx-font-size-xl); font-weight: var(--usx-font-weight-semibold); }
.system-page-note { color: var(--usx-color-on-surface-muted); font-size: var(--usx-font-size-base); }
.system-page-body { margin-top: var(--usx-spacing-md); }
.system-page-placeholder { display: flex; flex-direction: column; align-items: center; gap: var(--usx-spacing-md); padding: var(--usx-spacing-2xl); background: var(--usx-color-surface); border: 2px dashed var(--usx-color-border); border-radius: var(--usx-radius-lg); text-align: center; color: var(--usx-color-on-surface-muted); }
.system-page-placeholder-icon { font-size: var(--usx-font-size-3xl); }
.system-page-back-link { display: inline-block; margin-top: var(--usx-spacing-md); color: var(--usx-color-primary); font-size: var(--usx-font-size-sm); text-decoration: none; }
.system-page-back-link:hover { text-decoration: underline; }
</style>
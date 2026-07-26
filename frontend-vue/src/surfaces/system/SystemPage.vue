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
      <div v-if="resolvedPageCode.startsWith('S')" class="system-s-page-content">
        <div class="system-page-placeholder">
          <UIcon name="construction" class="system-page-placeholder-icon" />
          <p>S-page content module coming in Wave 2. This page ({{ resolvedPageCode }}) will host {{ pageMeta.title }}.</p>
        </div>
      </div>
    </div>

    <div v-else class="system-page-body">
      <p class="system-page-note">Unknown page: {{ pageCode }}. Not found in S-pages registry.</p>
      <router-link to="/system?tab=pages" class="system-page-back-link">← Back to Pages Browser</router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { SNACKBAR_BASE } from '../../api/base'
import UIcon from '../../skills/atoms/UIcon.vue'
import UBadge from '../../skills/atoms/UBadge.vue'

const API_BASE = SNACKBAR_BASE
const route = useRoute()

interface PageMeta { id: string; title: string; icon: string; description?: string }

// e.g. /system/s100 -> S100
const pageCode = computed(() => {
  const raw = String(route.params.pageId || '')
  return raw.toUpperCase() || 'UNKNOWN'
})

const LEGACY_P_TO_S_ALIAS: Record<string, string> = {
  P001: 'S340',
  P002: 'S340',
  P003: 'S340',
  P004: 'S340',
  P005: 'S340',
}

const resolvedPageCode = computed(() => LEGACY_P_TO_S_ALIAS[pageCode.value] || pageCode.value)

const LOCAL_FALLBACK_PAGES: PageMeta[] = [
  { id: 'S100', title: 'Tool Builder', icon: 'build' },
  { id: 'S101', title: 'Story Builder', icon: 'auto_stories' },
  { id: 'S300', title: 'Workflow Builder', icon: 'account_tree' },
  { id: 'S340', title: 'Operations Console', icon: 'tune' },
  { id: 'S310', title: 'Clipboard Orchestration', icon: 'content_paste' },
  { id: 'S320', title: 'Knowledge Tools', icon: 'psychology' },
  { id: 'S330', title: 'Migration Dashboard', icon: 'migration' },
  { id: 'S600', title: 'Learning Hub', icon: 'school' },
]
const pageMeta = ref<PageMeta | null>(null)

function applyPageMeta(pages: PageMeta[]) {
  const found = pages.find(p => p.id.toUpperCase() === resolvedPageCode.value)
  if (!found) return false
  pageMeta.value = {
    ...found,
    description: found.description || `${found.id} - ${found.title} system page.`,
  }
  return true
}

async function fetchPageMeta() {
  try {
    const res = await fetch(`${API_BASE}/api/system/pages`, { signal: AbortSignal.timeout(3000) })
    if (res.ok) {
      const data = await res.json()
      const pages: PageMeta[] = data.pages || []
      if (applyPageMeta(pages)) return
    }
  } catch {}

  applyPageMeta(LOCAL_FALLBACK_PAGES)
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
/**
 * @module stores/settings
 * @description Global settings — font, size, palette, light/dark.
 * Ported from useGlobalSettings.ts (React).
 */
import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { UCORE_BASE } from '../api/base'

export type FontStyle = 'inter' | 'system' | 'mono'
export type Palette = 'default' | 'ocean' | 'forest' | 'sunset'
export type ThemeMode = 'light' | 'dark' | 'auto'

export type TerminologyPack = 'standard' | 'storytelling'
const legacyTerminologyKey = 'ucore.document.terminology'

export const useSettingsStore = defineStore('settings', () => {
  const fontStyle = ref<FontStyle>('inter')
  const fontSize = ref<number>(16)
  const terminologyPack = ref<TerminologyPack>(
    localStorage.getItem(legacyTerminologyKey) === 'storytelling' ? 'storytelling' : 'standard',
  )
  const readingFont = ref<'serif' | 'sans'>('serif')
  function setReadingFont(value: 'serif' | 'sans') { readingFont.value = value }
  const palette = ref<Palette>('default')
  const themeMode = ref<ThemeMode>('dark')
  const defaultModel = ref('auto')
  const advancedView = ref(false)
  const initialized = ref(false)
  const syncError = ref('')
  let syncTimer: ReturnType<typeof setTimeout> | undefined

  function setFontStyle(style: FontStyle) {
    fontStyle.value = style
  }

  function setFontSize(size: number) {
    fontSize.value = Math.max(12, Math.min(24, size))
  }

  function setPalette(p: Palette) {
    palette.value = p
  }

  function setThemeMode(mode: ThemeMode) {
    themeMode.value = mode
  }

  function setDefaultModel(model: string) {
    defaultModel.value = model
  }

  function setAdvancedView(enabled: boolean) { advancedView.value = enabled }

  function applyPreferences(value: Record<string, unknown>) {
    if (value.terminologyPack === 'standard' || value.terminologyPack === 'storytelling') terminologyPack.value = value.terminologyPack
    if (value.readingFont === 'serif' || value.readingFont === 'sans') readingFont.value = value.readingFont
    if (typeof value.advancedView === 'boolean') advancedView.value = value.advancedView
    if (value.fontStyle === 'inter' || value.fontStyle === 'system' || value.fontStyle === 'mono') fontStyle.value = value.fontStyle
    if (typeof value.fontSize === 'number') setFontSize(value.fontSize)
    if (value.palette === 'default' || value.palette === 'ocean' || value.palette === 'forest' || value.palette === 'sunset') palette.value = value.palette
    if (value.themeMode === 'light' || value.themeMode === 'dark' || value.themeMode === 'auto') themeMode.value = value.themeMode
    if (typeof value.defaultModel === 'string') defaultModel.value = value.defaultModel
  }

  function snapshot() {
    return { terminologyPack: terminologyPack.value, readingFont: readingFont.value, fontStyle: fontStyle.value, fontSize: fontSize.value, palette: palette.value, themeMode: themeMode.value, defaultModel: defaultModel.value, advancedView: advancedView.value }
  }

  async function save() {
    try {
      const response = await fetch(`${UCORE_BASE}/api/user/preferences`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ preferences: snapshot() }), signal: AbortSignal.timeout(3000),
      })
      if (!response.ok) throw new Error(`Preferences returned ${response.status}`)
      localStorage.removeItem(legacyTerminologyKey)
      syncError.value = ''
    } catch (exc) {
      syncError.value = exc instanceof Error ? exc.message : 'Preference sync unavailable'
    }
  }

  async function initialize() {
    try {
      const response = await fetch(`${UCORE_BASE}/api/user/preferences`, { signal: AbortSignal.timeout(3000) })
      if (!response.ok) throw new Error(`Preferences returned ${response.status}`)
      const data = await response.json()
      const saved = data.preferences
      if (saved && Object.keys(saved).length) {
        applyPreferences(saved)
        if (saved.terminologyPack === undefined && localStorage.getItem(legacyTerminologyKey) !== null) {
          await save()
          return
        }
      } else {
        await save() // migrate the already-hydrated Pinia/localStorage state
        return
      }
      syncError.value = ''
    } catch (exc) {
      syncError.value = exc instanceof Error ? exc.message : 'Using local preferences'
    } finally {
      initialized.value = true
    }
  }

  function applyTheme() {
    const root = document.documentElement
    root.style.setProperty('--usx-font-size-base', `${fontSize.value}px`)
    root.style.setProperty('--usx-font-family-reading', readingFont.value === 'sans' ? 'var(--usx-font-family-sans, system-ui, sans-serif)' : 'var(--usx-font-family-serif, Charter, Georgia, serif)')
    root.setAttribute('data-theme', themeMode.value)
    root.setAttribute('data-palette', palette.value)
    root.setAttribute('data-font', fontStyle.value)
  }

  watch([fontStyle, fontSize, palette, themeMode, readingFont], applyTheme, { immediate: true })
  watch([fontStyle, fontSize, palette, themeMode, defaultModel, advancedView, readingFont, terminologyPack], () => {
    if (!initialized.value) return
    clearTimeout(syncTimer)
    syncTimer = setTimeout(() => void save(), 250)
  })

  return {
    terminologyPack,
    readingFont,
    setReadingFont,
    fontStyle,
    fontSize,
    palette,
    themeMode,
    defaultModel,
    advancedView,
    setAdvancedView,
    initialized,
    syncError,
    setFontStyle,
    setFontSize,
    setPalette,
    setThemeMode,
    setDefaultModel,
    initialize,
    save,
    applyTheme,
  }
}, {
  persist: true,
})

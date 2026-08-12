/**
 * @module stores/shell
 * @description App shell state — sidebar, chat panel, last surface.
 * Ported from SurfaceShellContext.tsx (React).
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'

export type ChatMode = 'closed' | 'panel' | 'floating'
export type TabOrientation = 'horizontal' | 'vertical'

export const useShellStore = defineStore('shell', () => {
  const sidebarOpen = ref(false)
  const developerSidebarOpen = ref(false)
  const developerSurfaceTab = ref<'code' | 'repository' | 'editor'>('code')
  const chatMode = ref<ChatMode>('floating')
  const lastSurface = ref<string>('/')
  const tabOrientation = ref<TabOrientation>('horizontal')
  const intelTab = ref<string>('chat')

  function toggleSidebar() {
    sidebarOpen.value = !sidebarOpen.value
  }

  function setSidebarOpen(open: boolean) {
    sidebarOpen.value = open
  }

  function toggleDeveloperSidebar() {
    if (developerSurfaceTab.value === 'code') return
    developerSidebarOpen.value = !developerSidebarOpen.value
  }

  function setDeveloperSidebarOpen(open: boolean) {
    developerSidebarOpen.value = open
  }

  function setDeveloperSurfaceTab(tab: 'code' | 'repository' | 'editor') {
    developerSurfaceTab.value = tab
  }

  function setChatMode(mode: ChatMode) {
    chatMode.value = mode
  }

  function toggleChat() {
    chatMode.value = chatMode.value === 'closed' ? 'floating' : 'closed'
  }

  function setLastSurface(route: string) {
    lastSurface.value = route
  }

  function setIntelTab(tab: string) {
    intelTab.value = tab
  }

  function toggleTabOrientation() {
    tabOrientation.value = tabOrientation.value === 'horizontal' ? 'vertical' : 'horizontal'
  }

  function setTabOrientation(orientation: TabOrientation) {
    tabOrientation.value = orientation
  }

  return {
    sidebarOpen,
    developerSidebarOpen,
    developerSurfaceTab,
    chatMode,
    lastSurface,
    tabOrientation,
    intelTab,
    toggleSidebar,
    setSidebarOpen,
    toggleDeveloperSidebar,
    setDeveloperSidebarOpen,
    setDeveloperSurfaceTab,
    setChatMode,
    toggleChat,
    setLastSurface,
    setIntelTab,
    toggleTabOrientation,
    setTabOrientation,
  }
})

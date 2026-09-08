/**
 * @module stores/shell
 * @description App shell state — sidebar, chat panel, last surface.
 * Ported from SurfaceShellContext.tsx (React).
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'

export type ChatMode = 'closed' | 'panel' | 'floating'
export type ChatPresentation = 'overlay' | 'toast' | 'sidebar' | 'floating'
export type TabOrientation = 'horizontal' | 'vertical'

export const useShellStore = defineStore('shell', () => {
  const sidebarOpen = ref(false)
  const developerSidebarOpen = ref(false)
  const developerSurfaceTab = ref<'code' | 'repository' | 'editor' | 'operations'>('code')
  const chatMode = ref<ChatMode>('closed')
  const chatPresentation = ref<ChatPresentation>(
    (localStorage.getItem('ucore-chat-presentation') as ChatPresentation) || 'overlay',
  )
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

  function setDeveloperSurfaceTab(tab: 'code' | 'repository' | 'editor' | 'operations') {
    developerSurfaceTab.value = tab
  }

  function setChatMode(mode: ChatMode) {
    chatMode.value = mode
  }

  function toggleChat() {
    chatMode.value = chatMode.value === 'closed' ? 'floating' : 'closed'
  }

  function setChatPresentation(presentation: ChatPresentation) {
    chatPresentation.value = presentation
    localStorage.setItem('ucore-chat-presentation', presentation)
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
    chatPresentation,
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
    setChatPresentation,
    setLastSurface,
    setIntelTab,
    toggleTabOrientation,
    setTabOrientation,
  }
})

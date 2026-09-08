import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { SNACKBAR_BASE } from '../api/base'

export type ChatIntent = 'ask' | 'plan' | 'act'
export interface DeveloperOperation {
  id: string; prompt: string; status: string; error?: string
  events: Array<{ type: string; update?: { sessionUpdate?: string; content?: { text?: string }; title?: string }; status?: string }>
  proposal?: { fingerprint: string; files: Array<{ path: string; patch: string; applied: boolean }> }
}
export interface DeveloperConversation {
  id: string; title: string; repository: string; mode: ChatIntent; status: string
  messages: Array<{ role: 'user' | 'assistant'; content: string }>
  events: Array<{ id: number; type: string; name?: string; status?: string; result?: unknown; run?: { action: string; status: string; output: string; exitCode: number | null } }>
  operationDetails: DeveloperOperation[]
}

export const useDeveloperChatStore = defineStore('developerChat', () => {
  const conversation = ref<DeveloperConversation | null>(null)
  const history = ref<Array<{ id: string; title: string; repository: string; status: string }>>([])
  const repository = ref('')
  const file = ref('')
  const suggestedRepository = ref('')
  const suggestedFile = ref('')
  const input = ref('')
  const intent = ref<ChatIntent>('ask')
  const error = ref('')
  const submitting = ref(false)
  const repos = ref<Array<{ name: string }>>([])
  const runtime = ref<{ available: boolean; model: string; provider: string; devMode: string } | null>(null)
  let stream: EventSource | null = null
  const busy = computed(() => submitting.value || conversation.value?.status === 'running')
  const working = computed(() => busy.value || conversation.value?.operationDetails.some(o => ['queued', 'running'].includes(o.status)))

  async function request(path: string, method = 'GET', body?: unknown) {
    const response = await fetch(`${SNACKBAR_BASE}/api/developer${path}`, {
      method, headers: { 'Content-Type': 'application/json' },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.error || 'Developer request failed')
    return data
  }
  function connect(id: string) {
    stream?.close()
    stream = new EventSource(`${SNACKBAR_BASE}/api/developer/conversations/${id}/events`)
    stream.onmessage = event => {
      if (conversation.value?.id === id) conversation.value = JSON.parse(event.data)
    }
    stream.onerror = () => { /* EventSource reconnects to a read-only snapshot stream. */ }
  }
  async function refreshHistory() {
    history.value = (await request('/conversations')).conversations
  }
  async function initialize() {
    try {
      const [capabilities, discovered] = await Promise.all([request('/operations/capabilities'), request('/repos')])
      runtime.value = capabilities; repos.value = discovered.repos
      await refreshHistory()
      const saved = localStorage.getItem('ucore-developer-conversation')
      if (!conversation.value && saved && history.value.some(item => item.id === saved)) await select(saved)
    } catch (cause) { error.value = String(cause) }
  }
  async function select(id: string) {
    try {
      conversation.value = await request(`/conversations/${id}`)
      repository.value = conversation.value!.repository
      intent.value = conversation.value!.mode
      file.value = ''; input.value = ''; error.value = ''
      localStorage.setItem('ucore-developer-conversation', id)
      connect(id)
    } catch (cause) { error.value = String(cause) }
  }
  function newConversation() {
    stream?.close(); stream = null
    conversation.value = null; input.value = ''; file.value = ''; intent.value = 'ask'
    repository.value = suggestedRepository.value
    localStorage.removeItem('ucore-developer-conversation')
  }
  async function send(text: string, mode: ChatIntent = intent.value) {
    if (busy.value) return
    submitting.value = true; error.value = ''
    try {
      conversation.value = await request('/chat', 'POST', {
        requestId: crypto.randomUUID(), conversationId: conversation.value?.id, workspace: repository.value,
        mode, message: text, context: file.value ? { file: file.value } : {},
      })
      intent.value = mode
      localStorage.setItem('ucore-developer-conversation', conversation.value!.id)
      connect(conversation.value!.id)
      await refreshHistory()
    } catch (cause) { error.value = String(cause); input.value = text }
    finally { submitting.value = false }
  }
  async function action(path: string, body: unknown = {}) {
    error.value = ''
    try {
      await request(path, 'POST', body)
      if (conversation.value) conversation.value = await request(`/conversations/${conversation.value.id}`)
    } catch (cause) { error.value = String(cause) }
  }
  async function stop() {
    if (conversation.value) await action(`/conversations/${conversation.value.id}/cancel`)
  }
  async function remove() {
    if (!conversation.value) return
    try {
      await request(`/conversations/${conversation.value.id}`, 'DELETE')
      newConversation(); await refreshHistory()
    } catch (cause) { error.value = String(cause) }
  }
  function useSelection() {
    if (!conversation.value) repository.value = suggestedRepository.value
    if (repository.value === suggestedRepository.value) file.value = suggestedFile.value
  }
  return { conversation, history, repository, file, suggestedRepository, suggestedFile, input, intent,
    error, repos, runtime, busy, working, initialize, select, newConversation, send, action, stop, remove, useSelection }
})

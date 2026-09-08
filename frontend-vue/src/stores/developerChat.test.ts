// @vitest-environment jsdom
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, afterEach, expect, it, vi } from 'vitest'
import { useDeveloperChatStore } from './developerChat'

beforeEach(() => {
  localStorage.clear(); setActivePinia(createPinia())
  vi.stubGlobal('EventSource', class { close() {} })
})
afterEach(() => vi.unstubAllGlobals())

it('sends repository and intent once without duplicating history or adding client authority', async () => {
  const response = { id: 'one', repository: 'demo', mode: 'plan', status: 'running', messages: [], events: [], operationDetails: [] }
  const fetchMock = vi.fn().mockResolvedValueOnce({ ok: true, json: async () => response })
    .mockResolvedValueOnce({ ok: true, json: async () => ({ conversations: [] }) })
  vi.stubGlobal('fetch', fetchMock)
  const chat = useDeveloperChatStore(); chat.repository = 'demo'
  await chat.send('Explain the bug', 'plan')
  const payload = JSON.parse(fetchMock.mock.calls[0][1].body)
  expect(payload).toMatchObject({ workspace: 'demo', message: 'Explain the bug', mode: 'plan' })
  expect(payload).not.toHaveProperty('history')
  expect(payload).not.toHaveProperty('model')
  expect(payload.requestId).toBeTruthy()
  expect(chat.conversation?.id).toBe('one')
})

it('preserves a submitted request when the backend refuses it', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, json: async () => ({ error: 'Enable full Dev Mode' }) }))
  const chat = useDeveloperChatStore(); chat.repository = 'demo'
  await chat.send('Fix this', 'act')
  expect(chat.input).toBe('Fix this')
  expect(chat.error).toContain('Enable full Dev Mode')
  expect(chat.busy).toBe(false)
})

it('does not retarget an existing conversation when workbench selection changes', () => {
  const chat = useDeveloperChatStore(); chat.repository = 'demo'
  chat.conversation = { id: 'one', title: 'one', repository: 'demo', mode: 'ask', status: 'completed', messages: [], events: [], operationDetails: [] }
  chat.suggestedRepository = 'other'; chat.suggestedFile = 'secret.py'
  chat.useSelection()
  expect(chat.repository).toBe('demo'); expect(chat.file).toBe('')
})

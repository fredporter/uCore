<template>
  <div class="bitchat-wrapper">
    <!-- Top Toolbar -->
    <header class="bitchat-toolbar">
      <div class="bitchat-toolbar__left">
        <h1 class="bitchat-title">BitChat</h1>
        <UBadge type="success" size="sm">Decentralized LAN Mesh</UBadge>
      </div>

      <div class="bitchat-toolbar__center">
        <div class="bitchat-status-indicator" :class="{ 'is-live': isWsConnected }">
          <span class="bitchat-status-dot"></span>
          <span class="bitchat-status-text font-mono">
            {{ isWsConnected ? 'LIVE MESH (WS)' : 'MESH POLLING' }}
          </span>
        </div>
        <span class="bitchat-node-info font-mono text-zinc-400 text-xs">
          Node: {{ localNodeName || 'Initializing...' }}
        </span>
      </div>

      <div class="bitchat-toolbar__right">
        <button class="usx-btn usx-btn--sm usx-btn--primary bitchat-btn bitchat-btn--accent" @click="triggerBeacon" :disabled="isBroadcasting">
          <UIcon name="cell_tower" />
          <span>{{ isBroadcasting ? 'Beaconing...' : 'Announce Beacon' }}</span>
        </button>
        <button class="usx-btn usx-btn--sm usx-btn--secondary bitchat-btn" @click="refreshAll" title="Refresh peers and messages">
          <UIcon name="refresh" />
          <span>Refresh</span>
        </button>
      </div>
    </header>

    <!-- Main Workspace Split Pane -->
    <div class="bitchat-workspace">
      <!-- Left Sidebar: Discovered Mesh Peers & Channels -->
      <aside class="bitchat-sidebar">
        <!-- Channel Selector -->
        <div class="bitchat-section">
          <div class="bitchat-section__header">
            <span class="bitchat-section__title">CHANNELS</span>
          </div>
          <div class="bitchat-channel-list">
            <button
              v-for="ch in channels"
              :key="ch.id"
              class="bitchat-channel-item"
              :class="{ active: currentChannel === ch.id }"
              @click="switchChannel(ch.id)"
            >
              <span class="bitchat-channel-hash">#</span>
              <span class="bitchat-channel-name">{{ ch.name }}</span>
              <span v-if="ch.id === currentChannel && messages.length > 0" class="bitchat-channel-badge font-mono">
                {{ messages.length }}
              </span>
            </button>
          </div>
        </div>

        <!-- Discovered Mesh Peers -->
        <div class="bitchat-section bitchat-section--peers">
          <div class="bitchat-section__header">
            <span class="bitchat-section__title">LAN MESH PEERS ({{ peers.length }})</span>
            <button class="bitchat-btn-mini font-mono" @click="loadPeers" title="Scan LAN Subnet">Scan</button>
          </div>

          <div class="bitchat-peer-list">
            <div v-if="peers.length === 0" class="bitchat-empty-peers font-mono text-zinc-500 text-xs p-3">
              Scanning local subnet...
            </div>
            <div
              v-for="peer in peers"
              :key="peer.peer_id"
              class="bitchat-peer-card"
              :class="{ 'is-local': peer.is_local }"
            >
              <div class="bitchat-peer-header">
                <span class="bitchat-peer-dot" :class="`peer-${peer.status}`"></span>
                <span class="bitchat-peer-name font-medium">{{ peer.node_name }}</span>
                <span v-if="peer.is_local" class="bitchat-badge-self font-mono">HOST</span>
              </div>
              <div class="bitchat-peer-meta font-mono text-zinc-400 text-xs">
                <span>{{ peer.ip }}:{{ peer.port }}</span>
                <span class="bitchat-peer-status font-semibold" :class="`status-text-${peer.status}`">
                  {{ peer.status.toUpperCase() }}
                </span>
              </div>
              <div v-if="peer.services" class="bitchat-peer-services">
                <span v-for="s in peer.services.slice(0, 2)" :key="s" class="bitchat-service-pill">
                  {{ s.replace('._tcp.local.', '') }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </aside>

      <!-- Center: Message Stream & Composer -->
      <main class="bitchat-main">
        <!-- Chat Header Bar -->
        <div class="bitchat-chat-header">
          <div class="bitchat-chat-title-group">
            <span class="bitchat-chat-title font-mono">{{ currentChannel }}</span>
            <span class="bitchat-chat-desc text-zinc-400 text-xs">
              Zero-cloud sovereign mesh conduit
            </span>
          </div>

          <!-- Selection Controls for "Save to Binder" -->
          <div class="bitchat-selection-actions">
            <span v-if="selectedMsgIds.length > 0" class="font-mono text-xs text-emerald-400">
              {{ selectedMsgIds.length }} selected
            </span>
            <button
              v-if="selectedMsgIds.length > 0"
              class="usx-btn usx-btn--sm usx-btn--primary bitchat-btn bitchat-btn--primary font-mono text-xs"
              @click="openSaveToBinderModal"
            >
              <UIcon name="folder" />
              <span>Save to Binder</span>
            </button>
            <button
              v-if="selectedMsgIds.length > 0"
              class="usx-btn usx-btn--sm usx-btn--secondary bitchat-btn bitchat-btn--ghost font-mono text-xs"
              @click="clearSelection"
            >
              Clear
            </button>
          </div>
        </div>

        <!-- Message Feed -->
        <div class="bitchat-feed" ref="feedEl">
          <div v-if="messages.length === 0" class="bitchat-empty-feed">
            <div class="bitchat-empty-icon">
              <UIcon name="forum" />
            </div>
            <div class="bitchat-empty-title">No messages in {{ currentChannel }} yet</div>
            <div class="bitchat-empty-subtitle text-zinc-400 text-xs">
              Broadcast a message across your local mesh network or save notes into your binders.
            </div>
          </div>

          <div
            v-for="msg in messages"
            :key="msg.msg_id"
            class="bitchat-msg"
            :class="{ 'is-selected': selectedMsgIds.includes(msg.msg_id) }"
          >
            <!-- Checkbox for multi-select -->
            <label class="bitchat-msg-select">
              <input
                type="checkbox"
                :checked="selectedMsgIds.includes(msg.msg_id)"
                @change="toggleSelectMessage(msg.msg_id)"
              />
            </label>

            <!-- Message Body -->
            <div class="bitchat-msg-content-wrap">
              <div class="bitchat-msg-header">
                <span class="bitchat-msg-sender font-medium">{{ msg.sender_name }}</span>
                <span class="bitchat-msg-time font-mono text-xs text-zinc-400">
                  {{ formatTimestamp(msg.timestamp) }}
                </span>
                <span v-if="msg.saved_to_binder" class="bitchat-tag bitchat-tag--saved font-mono" title="Saved to Binder Evidence">
                  <UIcon name="folder" /> EVIDENCE
                </span>
                <span v-if="msg.task_id" class="bitchat-tag bitchat-tag--task font-mono" title="Promoted to Sovereign Task">
                  <UIcon name="bolt" /> {{ msg.task_id }}
                </span>
              </div>

              <div class="bitchat-msg-body">{{ msg.content }}</div>

              <!-- Message Quick Actions -->
              <div class="bitchat-msg-actions">
                <button
                  class="usx-btn usx-btn--sm usx-btn--secondary bitchat-msg-btn font-mono"
                  @click="openConvertTaskModal(msg)"
                  title="Promote to .tasker markdown task"
                >
                  <UIcon name="bolt" /> Convert to Task
                </button>
                <button
                  class="usx-btn usx-btn--sm usx-btn--secondary bitchat-msg-btn font-mono"
                  @click="quickSaveSingleToBinder(msg)"
                  title="Save single message to binder evidence"
                >
                  <UIcon name="folder" /> Save to Binder
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Input Composer -->
        <footer class="bitchat-composer">
          <div class="bitchat-composer-sender">
            <label class="text-zinc-400 text-xs font-mono">From:</label>
            <input
              type="text"
              v-model="senderName"
              placeholder="Your identity..."
              class="bitchat-input-sender font-mono"
            />
          </div>

          <div class="bitchat-composer-input-row">
            <textarea
              v-model="draftText"
              @keydown.enter.exact.prevent="handleSendMessage"
              rows="2"
              placeholder="Type a message... (Press Enter to broadcast)"
              class="bitchat-textarea"
            ></textarea>

            <button
              class="usx-btn usx-btn--primary bitchat-btn bitchat-btn--send font-mono"
              :disabled="!draftText.trim()"
              @click="handleSendMessage"
            >
              <span>Send</span>
              <UIcon name="keyboard_return" />
            </button>
          </div>
        </footer>
      </main>
    </div>

    <!-- Modal: Save to Binder -->
    <div v-if="showSaveBinderModal" class="bitchat-modal-backdrop" @click.self="showSaveBinderModal = false">
      <div class="bitchat-modal">
        <div class="bitchat-modal-header">
          <h3>Save Discussion Evidence to Binder</h3>
          <button class="bitchat-modal-close" @click="showSaveBinderModal = false">
            <UIcon name="close" />
          </button>
        </div>
        <div class="bitchat-modal-body">
          <p class="text-xs text-zinc-400 mb-3">
            Exports {{ selectedMsgIds.length }} message(s) to
            <code>~/Vault/binders/&lt;binder&gt;/evidence/chats/</code> as Markdown.
          </p>

          <label class="bitchat-modal-label">Target Binder Name</label>
          <input
            type="text"
            v-model="binderName"
            placeholder="e.g. Sandbox, Research, ProjectX"
            class="bitchat-input mb-3"
          />

          <label class="bitchat-modal-label">Discussion Title</label>
          <input
            type="text"
            v-model="evidenceTitle"
            placeholder="e.g. Protocol Consensus & Architecture Notes"
            class="bitchat-input mb-3"
          />
        </div>
        <div class="bitchat-modal-footer">
          <button class="bitchat-btn bitchat-btn--ghost" @click="showSaveBinderModal = false">Cancel</button>
          <button class="bitchat-btn bitchat-btn--primary" :disabled="!binderName.trim()" @click="executeSaveToBinder">
            Save Evidence
          </button>
        </div>
      </div>
    </div>

    <!-- Modal: Convert to Task -->
    <div v-if="showConvertTaskModal" class="bitchat-modal-backdrop" @click.self="showConvertTaskModal = false">
      <div class="bitchat-modal">
        <div class="bitchat-modal-header">
          <h3>Convert Action Item to Task</h3>
          <button class="bitchat-modal-close" @click="showConvertTaskModal = false">
            <UIcon name="close" />
          </button>
        </div>
        <div class="bitchat-modal-body" v-if="activeTaskMsg">
          <div class="bitchat-task-preview mb-3 p-3 bg-zinc-900 border border-zinc-800 rounded">
            <span class="text-xs font-mono text-zinc-500">ORIGINAL MESSAGE:</span>
            <p class="text-sm mt-1 text-zinc-200">{{ activeTaskMsg.content }}</p>
          </div>

          <label class="bitchat-modal-label">Target Board</label>
          <select v-model="taskBoard" class="bitchat-input mb-3">
            <option value="inbox">Inbox</option>
            <option value="today">Today</option>
            <option value="backlog">Backlog</option>
          </select>

          <label class="bitchat-modal-label">Priority</label>
          <select v-model="taskPriority" class="bitchat-input mb-3">
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="urgent">Urgent</option>
          </select>

          <label class="bitchat-modal-label">Associated Binder</label>
          <input
            type="text"
            v-model="taskBinder"
            placeholder="e.g. Sandbox"
            class="bitchat-input mb-3"
          />

          <label class="bitchat-checkbox-row mb-3">
            <input type="checkbox" v-model="syncAppleReminders" />
            <span class="text-xs text-zinc-300">Bi-directional Sync to Apple Reminders (via Host PIM)</span>
          </label>
        </div>
        <div class="bitchat-modal-footer">
          <button class="bitchat-btn bitchat-btn--ghost" @click="showConvertTaskModal = false">Cancel</button>
          <button class="bitchat-btn bitchat-btn--primary" @click="executeConvertToTask">
            Create Sovereign Task
          </button>
        </div>
      </div>
    </div>

    <!-- Notification Toast -->
    <div v-if="toastMessage" class="bitchat-toast font-mono text-xs">
      {{ toastMessage }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import UIcon from '../../skills/atoms/UIcon.vue'
import UBadge from '../../skills/atoms/UBadge.vue'

// Channels
const channels = [
  { id: '#general', name: 'general' },
  { id: '#briefing', name: 'briefing' },
  { id: '#engineering', name: 'engineering' },
]
const currentChannel = ref('#general')

// State
const peers = ref<any[]>([])
const messages = ref<any[]>([])
const localPeerId = ref('')
const localNodeName = ref('')
const isWsConnected = ref(false)
const isBroadcasting = ref(false)
const senderName = ref('Host Node')
const draftText = ref('')
const selectedMsgIds = ref<string[]>([])
const toastMessage = ref<string | null>(null)
const feedEl = ref<HTMLElement | null>(null)

// Save to Binder Modal
const showSaveBinderModal = ref(false)
const binderName = ref('Sandbox')
const evidenceTitle = ref('Consensus Discussion')

// Convert to Task Modal
const showConvertTaskModal = ref(false)
const activeTaskMsg = ref<any | null>(null)
const taskBoard = ref('inbox')
const taskPriority = ref('medium')
const taskBinder = ref('Sandbox')
const syncAppleReminders = ref(false)

let ws: WebSocket | null = null
let peerPollInterval: any = null

function showToast(msg: string) {
  toastMessage.value = msg
  setTimeout(() => {
    if (toastMessage.value === msg) {
      toastMessage.value = null
    }
  }, 4000)
}

function formatTimestamp(ts: string) {
  if (!ts) return ''
  try {
    const d = new Date(ts)
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  } catch {
    return ts.slice(11, 19)
  }
}

// ── Networking & WebSockets ─────────────────────────────────────────

async function loadPeers() {
  try {
    const res = await fetch('/api/network/mesh/peers')
    if (res.ok) {
      const data = await res.json()
      localPeerId.value = data.local_peer_id || ''
      localNodeName.value = data.local_node_name || ''
      peers.value = data.peers || []
      if (!senderName.value || senderName.value === 'Host Node') {
        senderName.value = data.local_node_name || 'uDos Host'
      }
    }
  } catch (err) {
    console.debug('Failed to fetch mesh peers:', err)
  }
}

async function triggerBeacon() {
  isBroadcasting.value = true
  try {
    const res = await fetch('/api/network/mesh/announce', { method: 'POST' })
    if (res.ok) {
      const data = await res.json()
      showToast(`📡 Subnet beacon broadcast sent (${data.node_name})`)
      await loadPeers()
    }
  } catch (err) {
    showToast('Failed to broadcast beacon')
  } finally {
    isBroadcasting.value = false
  }
}

async function loadMessages(channel = currentChannel.value) {
  try {
    const encoded = encodeURIComponent(channel)
    const res = await fetch(`/api/network/bitchat/messages?channel=${encoded}&limit=100`)
    if (res.ok) {
      const data = await res.json()
      messages.value = data.messages || []
      await scrollToBottom()
    }
  } catch (err) {
    console.debug('Failed to fetch messages:', err)
  }
}

function connectWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${window.location.host}/api/network/bitchat/ws`

  try {
    ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      isWsConnected.value = true
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'chat_message') {
          if (data.channel === currentChannel.value) {
            messages.value.push(data.message)
            scrollToBottom()
          }
        } else if (data.type === 'peer_list') {
          peers.value = data.peers || []
        }
      } catch (err) {
        console.debug('WS parse error:', err)
      }
    }

    ws.onclose = () => {
      isWsConnected.value = false
      // Attempt reconnect after 4 seconds
      setTimeout(connectWebSocket, 4000)
    }

    ws.onerror = () => {
      isWsConnected.value = false
    }
  } catch (err) {
    isWsConnected.value = false
  }
}

async function scrollToBottom() {
  await nextTick()
  if (feedEl.value) {
    feedEl.value.scrollTop = feedEl.value.scrollHeight
  }
}

async function handleSendMessage() {
  const text = draftText.value.trim()
  if (!text) return

  draftText.value = ''

  // Attempt sending via WS if open
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({
      type: 'chat_message',
      channel: currentChannel.value,
      sender_name: senderName.value || 'Anonymous',
      content: text,
    }))
  } else {
    // HTTP fallback
    try {
      const res = await fetch('/api/network/bitchat/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sender_name: senderName.value || 'Anonymous',
          content: text,
          channel: currentChannel.value,
        }),
      })
      if (res.ok) {
        const data = await res.json()
        messages.value.push(data.message)
        await scrollToBottom()
      }
    } catch (err) {
      showToast('Failed to send message over mesh')
    }
  }
}

function switchChannel(channelId: string) {
  currentChannel.value = channelId
  selectedMsgIds.value = []
  loadMessages(channelId)
}

function toggleSelectMessage(msgId: string) {
  const idx = selectedMsgIds.value.indexOf(msgId)
  if (idx > -1) {
    selectedMsgIds.value.splice(idx, 1)
  } else {
    selectedMsgIds.value.push(msgId)
  }
}

function clearSelection() {
  selectedMsgIds.value = []
}

// ── Save to Binder Action ───────────────────────────────────────────

function openSaveToBinderModal() {
  if (selectedMsgIds.value.length === 0) return
  showSaveBinderModal.value = true
}

function quickSaveSingleToBinder(msg: any) {
  selectedMsgIds.value = [msg.msg_id]
  showSaveBinderModal.value = true
}

async function executeSaveToBinder() {
  if (!binderName.value.trim() || selectedMsgIds.value.length === 0) return

  try {
    const res = await fetch('/api/network/bitchat/save-to-binder', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        msg_ids: selectedMsgIds.value,
        binder: binderName.value.trim(),
        title: evidenceTitle.value.trim() || 'Discussion Evidence',
      }),
    })

    const data = await res.json()
    if (res.ok && data.ok) {
      showToast(`📁 Evidence saved to ${data.filename} (${data.binder})`)
      showSaveBinderModal.value = false
      selectedMsgIds.value = []
      // Refresh messages to show EVIDENCE badge
      await loadMessages()
    } else {
      showToast(`Save failed: ${data.error || 'Unknown error'}`)
    }
  } catch (err) {
    showToast('Failed to save evidence into binder')
  }
}

// ── Convert to Task Action ──────────────────────────────────────────

function openConvertTaskModal(msg: any) {
  activeTaskMsg.value = msg
  showConvertTaskModal.value = true
}

async function executeConvertToTask() {
  if (!activeTaskMsg.value) return

  try {
    const res = await fetch('/api/network/bitchat/convert-to-task', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        msg_id: activeTaskMsg.value.msg_id,
        board: taskBoard.value,
        priority: taskPriority.value,
        binder: taskBinder.value,
        sync_apple_reminders: syncAppleReminders.value,
      }),
    })

    const data = await res.json()
    if (res.ok && data.ok) {
      showToast(`⚡ Sovereign Task ${data.task_id} created in ${taskBoard.value}!`)
      showConvertTaskModal.value = false
      activeTaskMsg.value = null
      await loadMessages()
    } else {
      showToast(`Task creation failed: ${data.error || 'Unknown error'}`)
    }
  } catch (err) {
    showToast('Failed to create task')
  }
}

function refreshAll() {
  loadPeers()
  loadMessages()
}

onMounted(() => {
  loadPeers()
  loadMessages()
  connectWebSocket()
  peerPollInterval = setInterval(loadPeers, 10000)
})

onUnmounted(() => {
  if (peerPollInterval) clearInterval(peerPollInterval)
  if (ws) {
    ws.onclose = null
    ws.close()
  }
})
</script>

<style scoped>
.bitchat-wrapper {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--usx-color-bg, #0b0c0e);
  color: var(--usx-color-text, #e2e4e9);
  font-family: var(--usx-font-sans, system-ui, sans-serif);
}

.bitchat-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1.25rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(18, 20, 24, 0.95);
  backdrop-filter: blur(8px);
}

.bitchat-toolbar__left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.bitchat-title {
  font-size: 1.15rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.bitchat-badge {
  font-size: 0.7rem;
  padding: 0.15rem 0.45rem;
  background: rgba(16, 185, 129, 0.15);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.3);
  border-radius: 3px;
}

.bitchat-toolbar__center {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.bitchat-status-indicator {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.2rem 0.6rem;
  border-radius: 9999px;
  background: rgba(245, 158, 11, 0.1);
  border: 1px solid rgba(245, 158, 11, 0.3);
  color: #fbbf24;
}

.bitchat-status-indicator.is-live {
  background: rgba(16, 185, 129, 0.1);
  border-color: rgba(16, 185, 129, 0.3);
  color: #34d399;
}

.bitchat-status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.bitchat-toolbar__right {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.bitchat-btn {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: var(--usx-color-text, #e2e4e9);
  padding: 0.4rem 0.8rem;
  border-radius: 4px;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.15s ease;
}

.bitchat-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.12);
}

.bitchat-btn--accent {
  background: rgba(59, 130, 246, 0.2);
  border-color: rgba(59, 130, 246, 0.4);
  color: #60a5fa;
}

.bitchat-btn--accent:hover:not(:disabled) {
  background: rgba(59, 130, 246, 0.3);
}

.bitchat-btn--primary {
  background: rgba(16, 185, 129, 0.25);
  border-color: rgba(16, 185, 129, 0.5);
  color: #34d399;
}

.bitchat-btn--primary:hover:not(:disabled) {
  background: rgba(16, 185, 129, 0.35);
}

.bitchat-btn--ghost {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.bitchat-btn-mini {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: #9ca3af;
  padding: 0.1rem 0.35rem;
  border-radius: 3px;
  font-size: 0.65rem;
  cursor: pointer;
}

.bitchat-btn-mini:hover {
  color: #fff;
  border-color: #fff;
}

/* ── Workspace ── */
.bitchat-workspace {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.bitchat-sidebar {
  width: 280px;
  min-width: 240px;
  border-right: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(14, 15, 18, 0.85);
  display: flex;
  flex-direction: column;
}

.bitchat-section {
  padding: 1rem 0.75rem;
}

.bitchat-section--peers {
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  flex: 1;
  overflow-y: auto;
}

.bitchat-section__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  padding: 0 0.25rem;
}

.bitchat-section__title {
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  color: #6b7280;
}

.bitchat-channel-list {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.bitchat-channel-item {
  display: flex;
  align-items: center;
  width: 100%;
  padding: 0.4rem 0.6rem;
  background: transparent;
  border: none;
  border-radius: 4px;
  color: #9ca3af;
  cursor: pointer;
  font-size: 0.85rem;
  text-align: left;
  transition: all 0.15s ease;
}

.bitchat-channel-item:hover {
  background: rgba(255, 255, 255, 0.04);
  color: #e2e4e9;
}

.bitchat-channel-item.active {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
  font-weight: 600;
}

.bitchat-channel-hash {
  color: #4b5563;
  margin-right: 0.4rem;
  font-weight: bold;
}

.bitchat-channel-name {
  flex: 1;
}

.bitchat-channel-badge {
  font-size: 0.65rem;
  padding: 0.1rem 0.35rem;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 9999px;
  color: #9ca3af;
}

.bitchat-peer-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.bitchat-peer-card {
  padding: 0.6rem;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.bitchat-peer-card.is-local {
  border-color: rgba(59, 130, 246, 0.25);
  background: rgba(59, 130, 246, 0.04);
}

.bitchat-peer-header {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin-bottom: 0.2rem;
}

.bitchat-peer-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.peer-online { background: #34d399; }
.peer-idle { background: #fbbf24; }
.peer-offline { background: #6b7280; }

.status-text-online { color: #34d399; }
.status-text-idle { color: #fbbf24; }
.status-text-offline { color: #6b7280; }

.bitchat-peer-name {
  font-size: 0.8rem;
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.bitchat-badge-self {
  font-size: 0.6rem;
  padding: 0.05rem 0.25rem;
  border-radius: 2px;
  background: rgba(59, 130, 246, 0.2);
  color: #60a5fa;
}

.bitchat-peer-meta {
  display: flex;
  justify-content: space-between;
}

.bitchat-peer-services {
  display: flex;
  gap: 0.25rem;
  margin-top: 0.3rem;
  flex-wrap: wrap;
}

.bitchat-service-pill {
  font-size: 0.6rem;
  font-family: monospace;
  background: rgba(255, 255, 255, 0.05);
  color: #9ca3af;
  padding: 0.05rem 0.25rem;
  border-radius: 2px;
}

/* ── Main Chat Pane ── */
.bitchat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--usx-color-bg, #0b0c0e);
}

.bitchat-chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1.25rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.bitchat-chat-title {
  font-size: 1rem;
  font-weight: 700;
  margin-right: 0.75rem;
}

.bitchat-selection-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.bitchat-feed {
  flex: 1;
  overflow-y: auto;
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.bitchat-empty-feed {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  color: #6b7280;
}

.bitchat-empty-icon {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
}

.bitchat-empty-title {
  font-size: 1rem;
  font-weight: 600;
  color: #9ca3af;
}

.bitchat-msg {
  display: flex;
  gap: 0.75rem;
  padding: 0.75rem;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.04);
  transition: all 0.15s ease;
}

.bitchat-msg:hover {
  background: rgba(255, 255, 255, 0.04);
}

.bitchat-msg.is-selected {
  background: rgba(16, 185, 129, 0.05);
  border-color: rgba(16, 185, 129, 0.3);
}

.bitchat-msg-select input {
  cursor: pointer;
  accent-color: #10b981;
}

.bitchat-msg-content-wrap {
  flex: 1;
}

.bitchat-msg-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.35rem;
}

.bitchat-msg-sender {
  font-size: 0.85rem;
  color: #e5e7eb;
}

.bitchat-tag {
  font-size: 0.6rem;
  padding: 0.05rem 0.3rem;
  border-radius: 2px;
}

.bitchat-tag--saved {
  background: rgba(16, 185, 129, 0.15);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.bitchat-tag--task {
  background: rgba(245, 158, 11, 0.15);
  color: #fbbf24;
  border: 1px solid rgba(245, 158, 11, 0.3);
}

.bitchat-msg-body {
  font-size: 0.9rem;
  line-height: 1.5;
  color: #d1d5db;
  white-space: pre-wrap;
  word-break: break-word;
}

.bitchat-msg-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
  opacity: 0.4;
  transition: opacity 0.15s ease;
}

.bitchat-msg:hover .bitchat-msg-actions {
  opacity: 1;
}

.bitchat-msg-btn {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #9ca3af;
  font-size: 0.68rem;
  padding: 0.15rem 0.45rem;
  border-radius: 3px;
  cursor: pointer;
}

.bitchat-msg-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}

/* ── Composer ── */
.bitchat-composer {
  padding: 0.75rem 1.25rem 1rem 1.25rem;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(14, 15, 18, 0.95);
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.bitchat-composer-sender {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.bitchat-input-sender {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #e2e4e9;
  font-size: 0.75rem;
  padding: 0.15rem 0.45rem;
  border-radius: 3px;
  width: 140px;
}

.bitchat-composer-input-row {
  display: flex;
  gap: 0.5rem;
}

.bitchat-textarea {
  flex: 1;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 4px;
  color: #e2e4e9;
  font-size: 0.88rem;
  padding: 0.5rem 0.75rem;
  outline: none;
  resize: none;
  font-family: inherit;
}

.bitchat-textarea:focus {
  border-color: rgba(59, 130, 246, 0.5);
}

.bitchat-btn--send {
  background: #2563eb;
  color: #fff;
  border: none;
  padding: 0 1.25rem;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
  transition: background 0.15s ease;
}

.bitchat-btn--send:hover:not(:disabled) {
  background: #1d4ed8;
}

.bitchat-btn--send:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* ── Modals ── */
.bitchat-modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
  backdrop-filter: blur(4px);
}

.bitchat-modal {
  background: #13151a;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  width: 440px;
  max-width: 90vw;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
  overflow: hidden;
}

.bitchat-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.85rem 1.25rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.bitchat-modal-header h3 {
  font-size: 0.95rem;
  font-weight: 600;
  margin: 0;
}

.bitchat-modal-close {
  background: transparent;
  border: none;
  color: #9ca3af;
  font-size: 1.2rem;
  cursor: pointer;
}

.bitchat-modal-body {
  padding: 1.25rem;
}

.bitchat-modal-label {
  display: block;
  font-size: 0.75rem;
  font-weight: 600;
  color: #9ca3af;
  margin-bottom: 0.25rem;
}

.bitchat-input {
  width: 100%;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #e2e4e9;
  font-size: 0.85rem;
  padding: 0.45rem 0.65rem;
  border-radius: 4px;
  outline: none;
  box-sizing: border-box;
}

.bitchat-checkbox-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.bitchat-checkbox-row input {
  accent-color: #10b981;
}

.bitchat-modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  padding: 0.75rem 1.25rem;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(0, 0, 0, 0.2);
}

/* ── Toast ── */
.bitchat-toast {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  background: #1f2937;
  color: #f3f4f6;
  border: 1px solid #374151;
  padding: 0.6rem 1rem;
  border-radius: 6px;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
  z-index: 1000;
}
</style>

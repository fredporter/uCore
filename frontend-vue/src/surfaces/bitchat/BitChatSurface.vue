<template>
  <div class="bitchat-wrapper">
    <!-- Top Toolbar -->
    <header class="bitchat-toolbar">
      <div class="bitchat-toolbar__left">
        <h1 class="bitchat-title">BitChat</h1>
        <p>Local mesh messaging</p>
      </div>

      <div class="bitchat-toolbar__center">
        <div class="bitchat-status-indicator" :class="{ 'is-live': isWsConnected }">
          <span class="bitchat-status-dot"></span>
          <span class="bitchat-status-text">
            {{ isWsConnected ? 'Live mesh' : 'Polling mesh' }}
          </span>
        </div>
        <span class="bitchat-node-info">
          Node: {{ localNodeName || 'Initializing...' }}
        </span>
      </div>

      <div class="bitchat-toolbar__right">
        <button class="usx-btn usx-btn--sm usx-btn--primary" @click="triggerBeacon" :disabled="isBroadcasting">
          <UIcon name="cell_tower" />
          <span>{{ isBroadcasting ? 'Beaconing...' : 'Announce Beacon' }}</span>
        </button>
        <button class="usx-btn usx-btn--sm usx-btn--secondary" @click="refreshAll" title="Refresh peers and messages">
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
              class="usx-btn bitchat-channel-item"
              :aria-pressed="currentChannel === ch.id"
              @click="switchChannel(ch.id)"
            >
              <UIcon name="tag" aria-hidden="true" />
              <span class="bitchat-channel-name">{{ ch.name }}</span>
              <span v-if="ch.id === currentChannel && messages.length > 0" class="bitchat-channel-badge">
                {{ messages.length }}
              </span>
            </button>
          </div>
        </div>

        <!-- Discovered Mesh Peers -->
        <div class="bitchat-section bitchat-section--peers">
          <div class="bitchat-section__header">
            <span class="bitchat-section__title">LAN MESH PEERS ({{ peers.length }})</span>
            <button class="usx-btn usx-btn--sm" @click="loadPeers" title="Refresh LAN peers"><UIcon name="radar" /> Scan</button>
          </div>

          <div class="bitchat-peer-list">
            <div v-if="peers.length === 0" class="bitchat-empty-peers">
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
                <span class="bitchat-peer-name">{{ peer.node_name }}</span>
                <span v-if="peer.is_local" class="bitchat-badge-self">HOST</span>
              </div>
              <div class="bitchat-peer-meta">
                <span>{{ peer.ip }}:{{ peer.port }}</span>
                <span class="bitchat-peer-status" :class="`status-text-${peer.status}`">
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
      <section class="bitchat-main" aria-label="Conversation">
        <!-- Chat Header Bar -->
        <div class="bitchat-chat-header">
          <div class="bitchat-chat-title-group">
            <span class="bitchat-chat-title">{{ currentChannel }}</span>
            <span class="bitchat-chat-desc">
              Nearby messaging
            </span>
          </div>

          <!-- Selection Controls for "Save to Binder" -->
          <div class="bitchat-selection-actions">
            <span v-if="selectedMsgIds.length > 0" class="bitchat-muted">
              {{ selectedMsgIds.length }} selected
            </span>
            <button
              v-if="selectedMsgIds.length > 0"
              class="usx-btn usx-btn--sm usx-btn--primary"
              @click="openSaveToBinderModal"
            >
              <UIcon name="folder" />
              <span>Save to Binder</span>
            </button>
            <button
              v-if="selectedMsgIds.length > 0"
              class="usx-btn usx-btn--sm usx-btn--secondary"
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
            <div class="bitchat-empty-subtitle">
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
                :aria-label="`Select message from ${msg.sender_name}`"
                @change="toggleSelectMessage(msg.msg_id)"
              />
            </label>

            <div class="bitchat-msg-header">
              <span class="bitchat-msg-sender">{{ msg.sender_name }}</span>
              <span class="bitchat-msg-time">
                {{ formatTimestamp(msg.timestamp) }}
              </span>
              <span v-if="msg.saved_to_binder" class="bitchat-tag bitchat-tag--saved" title="Saved to Binder Evidence">
                <UIcon name="folder" /> EVIDENCE
              </span>
              <span v-if="msg.task_id" class="bitchat-tag bitchat-tag--task" title="Linked task">
                <UIcon name="bolt" /> {{ msg.task_id }}
              </span>
            </div>

            <div class="bitchat-msg-body">{{ msg.content }}</div>

            <!-- Message Quick Actions -->
            <div class="bitchat-msg-actions">
              <button
                class="usx-btn usx-btn--sm usx-btn--secondary"
                @click="openConvertTaskModal(msg)"
                title="Promote to .tasker markdown task"
              >
                <UIcon name="bolt" /> Convert to Task
              </button>
              <button
                class="usx-btn usx-btn--sm usx-btn--secondary"
                @click="quickSaveSingleToBinder(msg)"
                title="Save single message to binder evidence"
              >
                <UIcon name="folder" /> Save to Binder
              </button>
            </div>
          </div>
        </div>

        <!-- Input Composer -->
        <footer class="bitchat-composer">
          <div class="bitchat-composer-sender">
            <label class="bitchat-muted" for="bitchat-sender">From</label>
            <input
              type="text"
              id="bitchat-sender"
              v-model="senderName"
              placeholder="Your identity..."
              class="bitchat-input-sender"
            />
          </div>

          <div class="bitchat-composer-input-row">
            <textarea
              v-model="draftText"
              @keydown.enter.exact.prevent="handleSendMessage"
              rows="2"
              placeholder="Type a message... (Press Enter to broadcast)"
              class="bitchat-textarea"
              aria-label="Message"
            ></textarea>

            <button
              class="usx-btn usx-btn--primary bitchat-send"
              :disabled="!draftText.trim()"
              @click="handleSendMessage"
            >
              <span>Send</span>
              <UIcon name="keyboard_return" />
            </button>
          </div>
        </footer>
      </section>
    </div>

    <!-- Modal: Save to Binder -->
    <div v-if="showSaveBinderModal" class="bitchat-modal-backdrop" @click.self="showSaveBinderModal = false">
      <div class="bitchat-modal" role="dialog" aria-modal="true" aria-labelledby="bitchat-save-heading">
        <div class="bitchat-modal-header">
          <h3 id="bitchat-save-heading">Save Discussion Evidence to Binder</h3>
          <button class="usx-btn usx-btn--ghost bitchat-modal-close" aria-label="Close" @click="showSaveBinderModal = false">
            <UIcon name="close" />
          </button>
        </div>
        <div class="bitchat-modal-body">
          <p class="bitchat-muted">
            Saves {{ selectedMsgIds.length }} message(s) as Markdown. Leave Binder blank to save in Sandbox.
          </p>

          <label class="bitchat-modal-label" for="bitchat-binder-id">Binder ID (optional)</label>
          <input
            type="text"
            id="bitchat-binder-id" v-model="binderName"
            placeholder="e.g. research"
            class="bitchat-input"
          />

          <label class="bitchat-modal-label" for="bitchat-evidence-title">Discussion Title</label>
          <input
            type="text"
            id="bitchat-evidence-title" v-model="evidenceTitle"
            placeholder="e.g. Protocol Consensus & Architecture Notes"
            class="bitchat-input"
          />
        </div>
        <div class="bitchat-modal-footer">
          <button class="usx-btn usx-btn--secondary" @click="showSaveBinderModal = false">Cancel</button>
          <button class="usx-btn usx-btn--primary" @click="executeSaveToBinder">
            Save Evidence
          </button>
        </div>
      </div>
    </div>

    <!-- Modal: Convert to Task -->
    <div v-if="showConvertTaskModal" class="bitchat-modal-backdrop" @click.self="showConvertTaskModal = false">
      <div class="bitchat-modal" role="dialog" aria-modal="true" aria-labelledby="bitchat-task-heading">
        <div class="bitchat-modal-header">
          <h3 id="bitchat-task-heading">Convert Action Item to Task</h3>
          <button class="usx-btn usx-btn--ghost bitchat-modal-close" aria-label="Close" @click="showConvertTaskModal = false">
            <UIcon name="close" />
          </button>
        </div>
        <div class="bitchat-modal-body" v-if="activeTaskMsg">
          <div class="bitchat-task-preview">
            <span>ORIGINAL MESSAGE:</span>
            <p>{{ activeTaskMsg.content }}</p>
          </div>

          <label class="bitchat-modal-label" for="bitchat-target-board">Target Board</label>
          <select id="bitchat-target-board" v-model="taskBoard" class="bitchat-input">
            <option value="inbox">Inbox</option>
            <option value="today">Today</option>
            <option value="backlog">Backlog</option>
          </select>

          <label class="bitchat-modal-label" for="bitchat-priority">Priority</label>
          <select id="bitchat-priority" v-model="taskPriority" class="bitchat-input">
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="urgent">Urgent</option>
          </select>

          <label class="bitchat-modal-label" for="bitchat-task-binder">Associated Binder</label>
          <input
            type="text"
            id="bitchat-task-binder" v-model="taskBinder"
            placeholder="Optional Binder ID"
            class="bitchat-input"
          />

          <label class="bitchat-checkbox-row">
            <input type="checkbox" v-model="syncAppleReminders" />
            <span>Bi-directional Sync to Apple Reminders (via Host PIM)</span>
          </label>
        </div>
        <div class="bitchat-modal-footer">
          <button class="usx-btn usx-btn--secondary" @click="showConvertTaskModal = false">Cancel</button>
          <button class="usx-btn usx-btn--primary" @click="executeConvertToTask">
            Create task
          </button>
        </div>
      </div>
    </div>

    <!-- Notification Toast -->
    <div v-if="toastMessage" class="bitchat-toast" role="status">
      {{ toastMessage }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import UIcon from '../../skills/atoms/UIcon.vue'

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
const binderName = ref('')
const evidenceTitle = ref('Consensus Discussion')

// Convert to Task Modal
const showConvertTaskModal = ref(false)
const activeTaskMsg = ref<any | null>(null)
const taskBoard = ref('inbox')
const taskPriority = ref('medium')
const taskBinder = ref('')
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
  if (selectedMsgIds.value.length === 0) return

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
      showToast(`⚡ Task ${data.task_id} created in ${taskBoard.value}!`)
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
  min-height: 0;
  background: var(--usx-color-background);
  color: var(--usx-color-on-surface);
  font-family: var(--usx-font-family-sans);
}

.bitchat-toolbar,
.bitchat-toolbar__left,
.bitchat-toolbar__center,
.bitchat-toolbar__right,
.bitchat-chat-header,
.bitchat-section__header,
.bitchat-selection-actions,
.bitchat-peer-header,
.bitchat-peer-meta,
.bitchat-peer-services,
.bitchat-msg-header,
.bitchat-msg-actions,
.bitchat-composer-sender,
.bitchat-composer-input-row,
.bitchat-modal-header,
.bitchat-modal-footer,
.bitchat-checkbox-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--usx-spacing-sm);
}

.bitchat-toolbar,
.bitchat-chat-header,
.bitchat-section__header,
.bitchat-peer-meta,
.bitchat-modal-header {
  justify-content: space-between;
}

.bitchat-toolbar,
.bitchat-chat-header,
.bitchat-composer,
.bitchat-modal-header,
.bitchat-modal-footer {
  padding: var(--usx-spacing-md);
  background: var(--usx-color-surface);
}

.bitchat-toolbar,
.bitchat-chat-header,
.bitchat-modal-header {
  border-block-end: var(--usx-border-width) solid var(--usx-color-border);
}

.bitchat-title,
.bitchat-toolbar p,
.bitchat-modal h3,
.bitchat-modal p {
  margin: 0;
}

.bitchat-title {
  font-size: var(--usx-font-size-lg);
}

.bitchat-toolbar p,
.bitchat-muted,
.bitchat-node-info,
.bitchat-peer-meta,
.bitchat-chat-desc,
.bitchat-empty-subtitle,
.bitchat-empty-peers,
.bitchat-msg-time {
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
}

.bitchat-status-indicator {
  display: inline-flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
}

.bitchat-status-indicator.is-live,
.status-text-online {
  color: var(--usx-color-success);
}

.bitchat-status-dot,
.bitchat-peer-dot {
  width: 0.45em;
  height: 0.45em;
  flex: none;
  border-radius: 50%;
  background: currentColor;
}

.peer-online { color: var(--usx-color-success); }
.peer-idle, .status-text-idle { color: var(--usx-color-warning); }
.peer-offline, .status-text-offline { color: var(--usx-color-on-surface-muted); }

.bitchat-workspace {
  display: grid;
  grid-template-columns: minmax(13rem, 24%) minmax(0, 1fr);
  flex: 1;
  min-height: 0;
}

.bitchat-sidebar {
  overflow: auto;
  border-inline-end: var(--usx-border-width) solid var(--usx-color-border);
  background: var(--usx-color-surface);
}

.bitchat-section,
.bitchat-channel-list,
.bitchat-peer-list,
.bitchat-peer-card,
.bitchat-composer,
.bitchat-modal-body {
  display: grid;
  gap: var(--usx-spacing-sm);
  min-width: 0;
}

.bitchat-section,
.bitchat-feed,
.bitchat-modal-body {
  padding: var(--usx-spacing-md);
}

.bitchat-section + .bitchat-section,
.bitchat-composer,
.bitchat-modal-footer {
  border-block-start: var(--usx-border-width) solid var(--usx-color-border);
}

.bitchat-section__title,
.bitchat-chat-title,
.bitchat-msg-sender,
.bitchat-peer-name {
  font-weight: var(--usx-font-weight-semibold);
}

.bitchat-wrapper .usx-btn {
  box-sizing: border-box;
  min-block-size: var(--usx-touch-min);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  gap: var(--usx-icon-gap);
  border-radius: var(--usx-radius-sm);
  font-size: var(--usx-font-size-sm);
  line-height: var(--usx-line-height-tight);
  box-shadow: none;
}

.bitchat-wrapper .usx-btn--secondary {
  background: var(--usx-color-surface);
}

.bitchat-wrapper .usx-btn--primary:hover:not(:disabled) {
  color: var(--usx-color-on-primary);
}

.bitchat-wrapper .usx-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.bitchat-wrapper .usx-btn:focus-visible {
  outline: 2px solid var(--usx-color-primary);
  outline-offset: 2px;
}

.usx-btn.bitchat-channel-item {
  width: 100%;
  justify-content: flex-start;
  border-color: transparent;
  background: transparent;
}

.usx-btn.bitchat-channel-item[aria-pressed="true"],
.bitchat-msg.is-selected {
  border-color: var(--usx-color-primary);
}

.usx-btn.bitchat-channel-item[aria-pressed="true"] {
  background: var(--usx-color-surface-variant);
  font-weight: var(--usx-font-weight-semibold);
}

.bitchat-channel-name { flex: 1; text-align: start; }

.bitchat-peer-card,
.bitchat-msg,
.bitchat-task-preview {
  padding: var(--usx-spacing-sm);
  background: var(--usx-color-surface);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  overflow-wrap: anywhere;
}

.bitchat-badge-self,
.bitchat-service-pill,
.bitchat-channel-badge,
.bitchat-tag {
  padding: var(--usx-spacing-xs);
  border-radius: var(--usx-radius-sm);
  background: var(--usx-color-surface-variant);
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-xs);
}

.bitchat-main,
.bitchat-feed {
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
}

.bitchat-feed {
  flex: 1;
  overflow: auto;
  gap: var(--usx-spacing-sm);
}

.bitchat-chat-title-group,
.bitchat-empty-feed {
  display: grid;
  gap: var(--usx-spacing-xs);
  min-width: 0;
}

.bitchat-empty-feed {
  margin: auto;
  text-align: center;
  justify-items: center;
}

.bitchat-msg {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  align-items: start;
  gap: var(--usx-spacing-sm);
}

.bitchat-msg-select { grid-column: 1; grid-row: 1; min-height: 0; }
.bitchat-msg > :not(.bitchat-msg-select) { grid-column: 2; min-width: 0; }
.bitchat-msg-body { white-space: pre-wrap; }
.bitchat-wrapper input[type="checkbox"] { accent-color: var(--usx-color-primary); }

.bitchat-input,
.bitchat-input-sender,
.bitchat-textarea {
  box-sizing: border-box;
  min-width: 0;
  max-width: 100%;
  padding: var(--usx-spacing-sm);
  background: var(--usx-color-background);
  color: var(--usx-color-on-surface);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  font: inherit;
}

.bitchat-input:focus-visible,
.bitchat-input-sender:focus-visible,
.bitchat-textarea:focus-visible {
  outline: var(--usx-border-width) solid var(--usx-color-primary);
  outline-offset: 1px;
}

.bitchat-textarea { width: 100%; resize: vertical; }
.bitchat-composer-input-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: end;
}

.bitchat-composer-input-row .bitchat-send { min-inline-size: 5.5rem; }

.bitchat-modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 999;
  display: grid;
  place-items: center;
  padding: var(--usx-spacing-md);
  background: color-mix(in srgb, var(--usx-color-background) 75%, transparent);
}

.bitchat-modal {
  width: min(100%, 28rem);
  max-height: 90dvh;
  overflow: auto;
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  background: var(--usx-color-surface);
}

.bitchat-modal-footer { justify-content: flex-end; }

.bitchat-toast {
  position: fixed;
  inset-block-end: var(--usx-spacing-lg);
  inset-inline-start: var(--usx-spacing-md);
  max-inline-size: calc(100% - 2 * var(--usx-spacing-md));
  z-index: 1000;
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: var(--usx-color-surface);
  overflow-wrap: anywhere;
}

@media (max-width: 680px) {
  .bitchat-wrapper { overflow: auto; }
  .bitchat-workspace { grid-template-columns: minmax(0, 1fr); flex: none; }
  .bitchat-sidebar {
    max-block-size: 14rem;
    border-inline-end: 0;
    border-block-end: var(--usx-border-width) solid var(--usx-color-border);
  }
  .bitchat-main { min-block-size: 24rem; }
  .bitchat-feed { max-block-size: 50dvh; }
}
</style>

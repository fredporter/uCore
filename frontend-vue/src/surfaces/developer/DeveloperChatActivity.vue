<template>
  <section class="dev-chat-activity" aria-label="Developer activity">
    <p v-if="chat.error" role="alert">{{ chat.error }}</p>
    <div v-if="chat.working" class="dev-chat-actions">
      <span>Developer work is running</span><button @click="chat.stop()">Stop</button>
    </div>
    <template v-if="chat.conversation">
      <p role="status">{{ chat.conversation.status }}</p>
      <details v-if="chat.conversation.events.length">
        <summary>Investigation and checks</summary>
        <ol>
          <li v-for="event in chat.conversation.events.filter(e => e.type === 'tool' || e.type === 'check')" :key="event.id">
            <span>{{ event.name || event.run?.action }} · {{ event.status || event.run?.status }}</span>
            <pre v-if="event.run">{{ event.run.output }}
Exit: {{ event.run.exitCode ?? 'pending' }}</pre>
            <details v-else-if="event.result"><summary>Result</summary><pre>{{ JSON.stringify(event.result, null, 2) }}</pre></details>
          </li>
        </ol>
      </details>
      <article v-for="operation in chat.conversation.operationDetails" :key="operation.id">
        <p><strong>{{ operation.status.replaceAll('_', ' ') }}</strong> — {{ operation.prompt }}</p>
        <p v-if="operation.error" role="alert">{{ operation.error }}</p>
        <div v-if="operation.status === 'awaiting_approval'" class="dev-chat-actions">
          <span>Construct a proposal for {{ chat.repository }} in an isolated workspace.</span>
          <button @click="chat.action(`/operations/${operation.id}/decision`, { decision: 'approve' })">Approve construction</button>
          <button @click="chat.action(`/operations/${operation.id}/decision`, { decision: 'deny' })">Deny</button>
        </div>
        <details v-if="operation.events.length">
          <summary>Construction activity</summary>
          <p v-for="(event, index) in operation.events" :key="index">{{ event.update?.content?.text || event.update?.title || event.status || event.update?.sessionUpdate }}</p>
        </details>
        <template v-if="operation.proposal?.files.length">
          <details v-for="file in operation.proposal.files" :key="file.path">
            <summary>{{ file.path }}{{ file.applied ? ' · applied' : '' }}</summary><pre>{{ file.patch }}</pre>
          </details>
          <button v-if="operation.status === 'completed' && operation.proposal.files.some(f => !f.applied)"
            @click="apply(operation.id, operation.proposal.fingerprint)">Apply reviewed changes</button>
        </template>
      </article>
      <button v-if="chat.intent !== 'act' && !chat.busy" @click="continueInAct">Continue in Act</button>
    </template>
  </section>
</template>
<script setup lang="ts">
import { useDeveloperChatStore } from '../../stores/developerChat'
const chat = useDeveloperChatStore()
function continueInAct() {
  chat.intent = 'act'
  chat.input = 'Implement the plan we just discussed. '
}
async function apply(id: string, fingerprint: string) {
  await chat.action(`/operations/${id}/proposal/apply`, { fingerprint })
  window.dispatchEvent(new CustomEvent('developer-proposal-applied', { detail: { repository: chat.repository } }))
}
</script>
<style scoped>
.dev-chat-activity { padding: var(--usx-space-3, 12px); font-size: var(--usx-text-sm, 13px); }
.dev-chat-activity article { border-top: 1px solid var(--usx-border, #555); padding-block: 12px; }
.dev-chat-activity pre { white-space: pre-wrap; overflow-wrap: anywhere; max-height: 320px; overflow: auto; }
.dev-chat-actions { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
.dev-chat-activity button { min-height: 36px; cursor: pointer; margin: 4px; }
</style>

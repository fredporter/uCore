<template>
  <section class="drone-grants" aria-label="Drone task access">
    <h3>Drone task access</h3>
    <p>Preview a Google Tasks list shared with your profile.</p>
    <form v-if="canManage" @submit.prevent="enroll">
      <label>Recipient
        <select v-model="recipient" required>
          <option value="">Choose a profile</option>
          <option v-for="profile in recipients" :key="profile.id" :value="profile.id">{{ profile.name }}</option>
        </select>
      </label>
      <label>Google account
        <select v-model="connectionId" required>
          <option value="">Choose an account</option>
          <option v-for="connection in eligibleConnections" :key="connection.id" :value="connection.id">{{ connection.health.account || connection.id.slice(0, 6) }}</option>
        </select>
      </label>
      <label>Task list
        <select v-model="listId" required>
          <option value="">Choose a task list</option>
          <option v-for="list in lists" :key="list" :value="list">{{ taskScope?.list_titles?.[list] || list }}</option>
        </select>
      </label>
      <label>Duration
        <select v-model.number="duration">
          <option :value="900">15 minutes</option><option :value="3600">1 hour</option><option :value="86400">24 hours</option>
        </select>
      </label>
      <button class="usx-btn" :disabled="busy || !recipient || !connectionId || !listId"><UIcon name="key" />Grant preview access</button>
    </form>
    <p v-if="error" role="alert">{{ error }}</p>
    <ul v-if="grants.length">
      <li v-for="grant in grants" :key="grant.id">
        {{ grant.recipient === identity.activeProfileId ? 'Shared with you' : 'Shared with ' + profileName(grant.recipient) }}
        <span v-if="grant.revoked"> · Revoked</span>
        <span v-else> · Expires {{ new Date(grant.expires * 1000).toLocaleString() }}</span>
        <button v-if="grant.recipient === identity.activeProfileId && !grant.revoked" class="usx-btn" :disabled="busy" @click="preview(grant.id)"><UIcon name="visibility" />Preview tasks</button>
        <button v-if="canManage && grant.owner === identity.activeProfileId && !grant.revoked" class="usx-btn" :disabled="busy" @click="revoke(grant.id)"><UIcon name="block" />Revoke</button>
      </li>
    </ul>
    <section v-if="result" aria-label="Shared Google Tasks preview">
      <h4>Shared Google Tasks</h4>
      <p v-if="!result.records.length">No tasks in this list.</p>
      <ul><li v-for="task in result.records" :key="task.id"><strong>{{ task.data.title }}</strong><p v-if="task.data.body">{{ task.data.body }}</p></li></ul>
      <p v-if="result.truncated">Showing the first 100 tasks.</p>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { UCORE_BASE } from '../../api/base';
import { useIdentityStore } from '../../stores/identity';
import UIcon from '../../skills/atoms/UIcon.vue';

interface Grant { id: string; owner: string; recipient: string; expires: number; revoked: number | null }
interface Connection { id: string; provider: string; health: { account?: string; state?: string }; config: { collections: { tasks?: { lists: string[]; list_titles?: Record<string, string> } } } }
interface Preview { records: { id: string; data: { title: string; body?: string } }[]; truncated: boolean }
const identity = useIdentityStore();
const grants = ref<Grant[]>([]);
const connections = ref<Connection[]>([]);
const canManage = ref(false);
const recipient = ref('');
const connectionId = ref('');
const listId = ref('');
const duration = ref(3600);
const result = ref<Preview | null>(null);
const busy = ref(false);
const error = ref('');
const recipients = computed(() => identity.profiles.filter(profile => profile.id !== identity.activeProfileId));
const eligibleConnections = computed(() => connections.value.filter(connection =>
  connection.provider === 'google' && connection.health.state !== 'disconnected' && connection.config.collections.tasks?.lists.length));
const taskScope = computed(() => eligibleConnections.value.find(connection => connection.id === connectionId.value)?.config.collections.tasks);
const lists = computed(() => taskScope.value?.lists || []);
watch(connectionId, () => { listId.value = ''; });

function profileName(id: string) { return identity.profiles.find(profile => profile.id === id)?.name || id; }
async function request(path: string, body?: object) {
  const response = await fetch(`${UCORE_BASE}/api/connections${path}`, body === undefined ? {} : {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error((await response.text()).slice(0, 250));
  return response.json();
}
async function run(action: (profile: string) => Promise<void>) {
  const profile = identity.activeProfileId;
  busy.value = true;
  error.value = '';
  try { await action(profile); }
  catch (failure) { if (identity.activeProfileId === profile) error.value = failure instanceof Error ? failure.message : 'Drone request failed'; }
  finally { if (identity.activeProfileId === profile) busy.value = false; }
}
async function load(profile: string) {
  const [status, shared] = await Promise.all([request(''), request('/drone/grants')]);
  if (identity.activeProfileId !== profile) return;
  canManage.value = status.drone_admin === true;
  connections.value = status.connections;
  grants.value = shared.grants;
}
function enroll() {
  void run(async profile => {
    await request('/drone/grants', { recipient: recipient.value, connection: connectionId.value, list: listId.value, duration: duration.value });
    await load(profile);
  });
}
function revoke(id: string) {
  void run(async profile => { await request(`/drone/grants/${id}/revoke`, {}); await load(profile); });
}
function preview(id: string) {
  result.value = null;
  void run(async profile => {
    const data = await request(`/drone/grants/${id}/preview`, {});
    if (identity.activeProfileId === profile) result.value = data;
  });
}
watch(() => identity.activeProfileId, profile => {
  result.value = null;
  grants.value = [];
  connections.value = [];
  canManage.value = false;
  recipient.value = '';
  connectionId.value = '';
  error.value = '';
  busy.value = false;
  if (profile) void run(load);
}, { immediate: true });
</script>

<style scoped>
.drone-grants { display: grid; gap: var(--usx-spacing-sm); min-width: 0; overflow-wrap: anywhere; }
form, label { display: grid; gap: var(--usx-spacing-sm); min-width: 0; }
form button { justify-self: start; }
li { margin-block: var(--usx-spacing-sm); }
</style>

<template>
  <div class="server-dashboard" v-if="!srv.loading">
    <!-- Header strip -->
    <div class="recipe-header">
      <div class="header-left">
        <span class="material-symbols-outlined header-icon">dashboard</span>
        <div>
          <h2 class="recipe-title">Server Overview</h2>
          <p class="recipe-desc">
            {{ srv.services.length }} services &middot; {{ srv.upCount }} online &middot; sovereign local runtime
          </p>
        </div>
      </div>
      <div class="header-meta">
        <span class="recipe-badge">Local-First (Zero Cloud Spend)</span>
      </div>
    </div>

    <!-- USX Card Matrix for System Metrics -->
    <div class="matrix-grid">
      <!-- Health Score -->
      <div class="matrix-card">
        <div class="card-top-row">
          <div class="icon-avatar" :class="`icon-avatar--${healthClass}`">
            <span class="material-symbols-outlined">health_and_safety</span>
          </div>
          <span class="card-tag">Overall</span>
        </div>
        <h3 class="card-title">System Health</h3>
        <p class="card-description">Aggregate availability across sovereign services and endpoints.</p>
        <div class="card-footer">
          <span class="card-metric" :class="`metric--${healthClass}`">{{ srv.healthPct }}%</span>
          <span class="card-metric-sub">Nominal</span>
        </div>
      </div>

      <!-- Online -->
      <div class="matrix-card">
        <div class="card-top-row">
          <div class="icon-avatar icon-avatar--success">
            <span class="material-symbols-outlined">check_circle</span>
          </div>
          <span class="card-tag card-tag--success">Normal</span>
        </div>
        <h3 class="card-title">Online Services</h3>
        <p class="card-description">Responding local daemons, Ollama runner, and background workers.</p>
        <div class="card-footer">
          <span class="card-metric metric--success">{{ srv.upCount }} Up</span>
          <span class="card-metric-sub">of {{ srv.services.length }} total</span>
        </div>
      </div>

      <!-- Degraded -->
      <div class="matrix-card">
        <div class="card-top-row">
          <div class="icon-avatar icon-avatar--warning">
            <span class="material-symbols-outlined">warning</span>
          </div>
          <span class="card-tag card-tag--warning">Investigate</span>
        </div>
        <h3 class="card-title">Degraded</h3>
        <p class="card-description">Services experiencing latency, throttling, or partial capability.</p>
        <div class="card-footer">
          <span class="card-metric metric--warning">{{ srv.degradedCount }} Degraded</span>
          <span class="card-metric-sub">Attention needed</span>
        </div>
      </div>

      <!-- Down -->
      <div class="matrix-card">
        <div class="card-top-row">
          <div class="icon-avatar icon-avatar--danger">
            <span class="material-symbols-outlined">error</span>
          </div>
          <span class="card-tag card-tag--danger">Down</span>
        </div>
        <h3 class="card-title">Offline</h3>
        <p class="card-description">Services stopped or unreachable on their designated local port.</p>
        <div class="card-footer">
          <span class="card-metric metric--danger">{{ srv.downCount }} Down</span>
          <span class="card-metric-sub">Action required</span>
        </div>
      </div>
    </div>

    <!-- USX Task List for Managed Services -->
    <div class="services-list-container">
      <div class="recipe-header">
        <div class="header-left">
          <span class="material-symbols-outlined header-icon">dns</span>
          <div>
            <h3 class="recipe-title">Managed Endpoints &amp; Services</h3>
            <p class="recipe-desc">Active process table monitored by uCore health probe</p>
          </div>
        </div>
        <div class="header-meta">
          <span class="recipe-badge">Interval: 15s</span>
        </div>
      </div>

      <div class="task-items-flow">
        <div
          v-for="svc in srv.services"
          :key="svc.name"
          class="task-item-card"
          :class="`status-${svc.status}`"
        >
          <!-- Status icon column -->
          <div class="task-item-icon-col">
            <span
              v-if="svc.status === 'up'"
              class="material-symbols-outlined status-icon icon-done"
            >check_circle</span>
            <span
              v-else-if="svc.status === 'degraded'"
              class="material-symbols-outlined status-icon icon-progress"
            >sync</span>
            <span
              v-else
              class="material-symbols-outlined status-icon icon-fail"
            >error</span>
          </div>

          <!-- Body -->
          <div class="task-item-body">
            <div class="task-title-row">
              <span class="task-title">{{ svc.name }}</span>
              <span class="task-badge" :class="`badge--${svc.status}`">
                {{ svc.status }}
              </span>
            </div>
            <p class="task-subtitle">{{ svc.description }}</p>

            <div class="task-footer">
              <div class="task-tags">
                <span class="task-tag-pill" v-if="svc.port">:{{ svc.port }}</span>
                <span class="task-tag-pill">{{ svc.type }}</span>
              </div>
              <span class="task-timestamp">{{ svc.uptime }}% uptime</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Active Product Launchers Matrix -->
    <div class="services-list-container">
      <div class="recipe-header">
        <div class="header-left">
          <span class="material-symbols-outlined header-icon">rocket_launch</span>
          <div>
            <h3 class="recipe-title">Ecosystem &amp; Host Launchers</h3>
            <p class="recipe-desc">Installed applications discovered on local host (absent products hidden)</p>
          </div>
        </div>
        <div class="header-meta">
          <span class="recipe-badge">{{ launchers.length }} Active</span>
        </div>
      </div>

      <div class="launchers-grid">
        <div v-for="l in launchers" :key="l.id" class="launcher-card">
          <div class="launcher-icon">
            <span class="material-symbols-outlined">{{ l.icon }}</span>
          </div>
          <div class="launcher-info">
            <div class="launcher-name">{{ l.name }}</div>
            <div class="launcher-desc">{{ l.description }}</div>
          </div>
          <span class="launcher-badge">{{ l.category }}</span>
        </div>
      </div>
    </div>

    <!-- Apple Activity & Bounded PIM Sync -->
    <div class="services-list-container">
      <div class="recipe-header">
        <div class="header-left">
          <span class="material-symbols-outlined header-icon">history_toggle_off</span>
          <div>
            <h3 class="recipe-title">Apple Activity &amp; Host PIM Sync</h3>
            <p class="recipe-desc">Bounded Calendar, Reminders, Notes &amp; Mail feed with anti-drift user annotation preservation</p>
          </div>
        </div>
        <div class="header-meta">
          <button
            class="sync-btn"
            :disabled="syncingActivity"
            @click="syncActivity"
          >
            <span class="material-symbols-outlined" :class="{ spinning: syncingActivity }">sync</span>
            {{ syncingActivity ? 'Syncing...' : 'Sync Activity' }}
          </button>
        </div>
      </div>

      <div v-if="syncMessage" class="sync-message">
        {{ syncMessage }}
      </div>

      <div v-if="activity && activity.events && activity.events.length" class="activity-events-list">
        <div v-for="ev in activity.events.slice(0, 8)" :key="ev.external_id" class="activity-row">
          <span class="activity-tag" :class="`activity-tag--${ev.source}`">{{ ev.source }}</span>
          <div class="activity-details">
            <strong>{{ ev.title }}</strong>
            <span class="activity-time">{{ ev.timestamp ? ev.timestamp.slice(0, 16).replace('T', ' ') : '' }}</span>
          </div>
        </div>
        <div class="activity-footer-note">
          Synced events recorded in <code>~/Vault/Activity/events.jsonl</code> · View <code>~/Vault/Activity/Daily_Activity.md</code>
        </div>
      </div>
      <div v-else class="activity-empty">
        <p>No activity events synced yet. Click "Sync Activity" to ingest local events into ~/Vault/Activity/.</p>
      </div>
    </div>
  </div>

  <div v-else class="server-loading">
    <span class="material-symbols-outlined spinning">progress_activity</span>
    <span>Loading sovereign server metrics...</span>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useSnackbarOpsStore } from "../../../stores/snackbarOps";

const srv = useSnackbarOpsStore();
const launchers = ref<any[]>([]);
const activity = ref<any>(null);
const syncingActivity = ref(false);
const syncMessage = ref("");

const healthClass = computed(() => {
  const pct = srv.healthPct;
  return pct >= 80
    ? "success"
    : pct >= 50
      ? "warning"
      : "danger";
});

async function fetchLaunchers() {
  try {
    const res = await fetch("/api/snackbar/launchers");
    if (res.ok) {
      const data = await res.json();
      launchers.value = data.launchers || [];
    }
  } catch (e) {
    // Non-blocking
  }
}

async function fetchActivity() {
  try {
    const res = await fetch("/api/snackbar/activity");
    if (res.ok) {
      activity.value = await res.json();
    }
  } catch (e) {
    // Non-blocking
  }
}

async function syncActivity() {
  syncingActivity.value = true;
  syncMessage.value = "";
  try {
    const res = await fetch("/api/snackbar/activity/sync", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sources: ["calendar", "mail"] }),
    });
    if (res.ok) {
      syncMessage.value = "Apple Activity synchronized cleanly into ~/Vault/Activity/Daily_Activity.md (user notes preserved).";
      await fetchActivity();
      setTimeout(() => { syncMessage.value = ""; }, 4000);
    } else {
      syncMessage.value = "Activity sync failed or permissions not granted.";
    }
  } catch (e: any) {
    syncMessage.value = `Sync error: ${e.message || e}`;
  } finally {
    syncingActivity.value = false;
  }
}

onMounted(() => {
  void fetchLaunchers();
  void fetchActivity();
});
</script>

<style scoped>
.server-dashboard {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  width: 100%;
}

.server-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 3rem;
  color: var(--usx-color-on-surface-variant, #8e9199);
  font-size: 0.9rem;
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* ── Recipe Header ── */
.recipe-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding-bottom: 0.85rem;
  border-bottom: 1px solid var(--usx-color-outline-variant, rgba(255, 255, 255, 0.1));
  flex-wrap: wrap;
  gap: 0.75rem;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.header-icon {
  font-size: 28px;
  color: var(--usx-color-primary, #a8c7fa);
}

.recipe-title {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--usx-color-on-surface, #e2e2e6);
}

.recipe-desc {
  margin: 0.25rem 0 0;
  font-size: 0.85rem;
  color: var(--usx-color-on-surface-variant, #8e9199);
}

.header-meta {
  display: flex;
  gap: 0.5rem;
}

.recipe-badge {
  font-size: 0.75rem;
  padding: 0.25rem 0.6rem;
  background: var(--usx-color-surface-container, rgba(255, 255, 255, 0.06));
  border-radius: 4px;
  color: var(--usx-color-on-surface-variant, #c4c6d0);
  font-family: var(--usx-font-family-mono, monospace);
}

/* ── USX Card Matrix ── */
.matrix-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 1rem;
  width: 100%;
}

.matrix-card {
  display: flex;
  flex-direction: column;
  padding: 1.25rem;
  border-radius: 12px;
  background: var(--usx-color-surface-container, rgba(255, 255, 255, 0.04));
  border: 1px solid var(--usx-color-outline-variant, rgba(255, 255, 255, 0.08));
  transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;
}

.matrix-card:hover {
  background: var(--usx-color-surface-container-high, rgba(255, 255, 255, 0.07));
  border-color: var(--usx-color-outline, rgba(255, 255, 255, 0.2));
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
}

.card-top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.icon-avatar {
  width: 38px;
  height: 38px;
  border-radius: 8px;
  background: rgba(168, 199, 250, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--usx-color-primary, #a8c7fa);
}

.icon-avatar .material-symbols-outlined {
  font-size: 20px;
}

.icon-avatar--success {
  background: rgba(63, 185, 80, 0.12);
  color: #3fb950;
}

.icon-avatar--warning {
  background: rgba(210, 153, 34, 0.12);
  color: #d29922;
}

.icon-avatar--danger {
  background: rgba(248, 81, 73, 0.12);
  color: #f85149;
}

.card-tag {
  font-size: 0.7rem;
  padding: 0.2rem 0.5rem;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.06);
  color: var(--usx-color-on-surface-variant, #c4c6d0);
  font-weight: 500;
}

.card-tag--success {
  background: rgba(63, 185, 80, 0.12);
  color: #3fb950;
}

.card-tag--warning {
  background: rgba(210, 153, 34, 0.12);
  color: #d29922;
}

.card-tag--danger {
  background: rgba(248, 81, 73, 0.12);
  color: #f85149;
}

.card-title {
  margin: 0 0 0.35rem;
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--usx-color-on-surface, #e2e2e6);
}

.card-description {
  margin: 0 0 1rem;
  font-size: 0.82rem;
  line-height: 1.4;
  color: var(--usx-color-on-surface-variant, #9aa0a6);
  flex: 1;
}

.card-footer {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  padding-top: 0.75rem;
  border-top: 1px solid var(--usx-color-outline-variant, rgba(255, 255, 255, 0.06));
}

.card-metric {
  font-size: 1.35rem;
  font-family: var(--usx-font-family-mono, monospace);
  font-weight: 700;
  color: var(--usx-color-on-surface, #e2e2e6);
}

.card-metric-sub {
  font-size: 0.75rem;
  color: var(--usx-color-on-surface-variant, #8e9199);
}

.metric--success { color: #3fb950; }
.metric--warning { color: #d29922; }
.metric--danger { color: #f85149; }

/* ── USX Task List for Services ── */
.services-list-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-top: 0.5rem;
}

.task-items-flow {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
  width: 100%;
}

.task-item-card {
  display: flex;
  align-items: flex-start;
  gap: 0.85rem;
  padding: 0.85rem 1.1rem;
  border-radius: 10px;
  background: var(--usx-color-surface-container, rgba(255, 255, 255, 0.03));
  border: 1px solid var(--usx-color-outline-variant, rgba(255, 255, 255, 0.08));
  transition: background 0.15s ease, border-color 0.15s ease;
}

.task-item-card:hover {
  background: var(--usx-color-surface-container-high, rgba(255, 255, 255, 0.06));
  border-color: var(--usx-color-outline, rgba(255, 255, 255, 0.18));
}

.task-item-icon-col {
  padding-top: 2px;
}

.status-icon {
  font-size: 20px;
}

.icon-done { color: #3fb950; }
.icon-progress {
  color: #58a6ff;
  animation: spin 3s linear infinite;
}
.icon-fail { color: #f85149; }

.task-item-body {
  flex: 1;
  min-width: 0;
}

.task-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.task-title {
  font-weight: 500;
  font-size: 0.92rem;
  color: var(--usx-color-on-surface, #e2e2e6);
}

.task-badge {
  font-size: 0.68rem;
  font-weight: 600;
  text-transform: uppercase;
  padding: 0.15rem 0.5rem;
  border-radius: 12px;
  letter-spacing: 0.03em;
}

.badge--up {
  background: rgba(63, 185, 80, 0.15);
  color: #3fb950;
}

.badge--degraded {
  background: rgba(210, 153, 34, 0.15);
  color: #d29922;
}

.badge--down {
  background: rgba(248, 81, 73, 0.15);
  color: #f85149;
}

.task-subtitle {
  margin: 0.25rem 0 0.5rem;
  font-size: 0.82rem;
  color: var(--usx-color-on-surface-variant, #9aa0a6);
  line-height: 1.4;
}

.task-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.75rem;
  gap: 0.5rem;
}

.task-tags {
  display: flex;
  gap: 0.35rem;
  flex-wrap: wrap;
}

.task-tag-pill {
  padding: 0.15rem 0.45rem;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.05);
  color: var(--usx-color-on-surface-variant, #8e9199);
  font-family: var(--usx-font-family-mono, monospace);
  font-size: 0.72rem;
}

.task-timestamp {
  color: var(--usx-color-on-surface-variant, #6e7681);
  font-size: 0.75rem;
}

/* ── Launchers Grid ── */
.launchers-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 0.85rem;
  padding: 0.5rem 0;
}

.launcher-card {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.85rem;
  background: var(--usx-color-surface-container, rgba(255, 255, 255, 0.03));
  border: 1px solid var(--usx-color-outline-variant, rgba(255, 255, 255, 0.08));
  border-radius: 8px;
  transition: all 0.15s ease;
}

.launcher-card:hover {
  background: var(--usx-color-surface-container-high, rgba(255, 255, 255, 0.06));
  border-color: var(--usx-color-primary, #a8c7fa);
}

.launcher-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 6px;
  background: rgba(168, 199, 250, 0.12);
  color: var(--usx-color-primary, #a8c7fa);
}

.launcher-info {
  flex: 1;
  min-width: 0;
}

.launcher-name {
  font-weight: 500;
  font-size: 0.88rem;
  color: var(--usx-color-on-surface, #e2e2e6);
}

.launcher-desc {
  font-size: 0.75rem;
  color: var(--usx-color-on-surface-variant, #8e9199);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.launcher-badge {
  font-size: 0.68rem;
  text-transform: uppercase;
  padding: 0.15rem 0.4rem;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.05);
  color: var(--usx-color-on-surface-variant, #8e9199);
}

/* ── Activity Feed ── */
.sync-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.35rem 0.75rem;
  background: var(--usx-color-primary, #a8c7fa);
  color: #0f172a;
  border: none;
  border-radius: 4px;
  font-size: 0.78rem;
  font-weight: 600;
  cursor: pointer;
}

.sync-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.sync-message {
  padding: 0.6rem 0.85rem;
  background: rgba(63, 185, 80, 0.12);
  border: 1px solid rgba(63, 185, 80, 0.3);
  color: #3fb950;
  border-radius: 6px;
  font-size: 0.82rem;
  margin-top: 0.5rem;
}

.activity-events-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.5rem 0;
}

.activity-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.6rem 0.75rem;
  background: var(--usx-color-surface-container, rgba(255, 255, 255, 0.03));
  border: 1px solid var(--usx-color-outline-variant, rgba(255, 255, 255, 0.06));
  border-radius: 6px;
}

.activity-tag {
  font-size: 0.7rem;
  text-transform: uppercase;
  font-weight: 600;
  padding: 0.15rem 0.45rem;
  border-radius: 4px;
}

.activity-tag--calendar { background: rgba(56, 189, 248, 0.15); color: #38bdf8; }
.activity-tag--reminders { background: rgba(234, 179, 8, 0.15); color: #eab308; }
.activity-tag--mail { background: rgba(168, 85, 247, 0.15); color: #a855f7; }
.activity-tag--notes { background: rgba(34, 197, 94, 0.15); color: #22c55e; }

.activity-details {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.85rem;
}

.activity-time {
  font-size: 0.75rem;
  color: var(--usx-color-on-surface-variant, #8e9199);
}

.activity-footer-note {
  font-size: 0.75rem;
  color: var(--usx-color-on-surface-variant, #8e9199);
  padding: 0.5rem 0;
  font-style: italic;
}

.activity-empty {
  padding: 1.5rem 0;
  text-align: center;
  color: var(--usx-color-on-surface-variant, #8e9199);
  font-size: 0.85rem;
}
</style>

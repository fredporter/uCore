<template>
  <div class="server-dashboard" v-if="!srv.loading">
    <!-- Header strip -->
    <div class="recipe-header">
      <div class="header-left">
        <span class="material-symbols-outlined header-icon">dashboard</span>
        <div>
          <h2 class="recipe-title">Server Overview</h2>
          <p class="recipe-desc">
            {{ srv.services.length }} services &middot; {{ srv.upCount }} online &middot; local
          </p>
        </div>
      </div>
      <div class="header-meta">
        <span class="recipe-badge">Local processing</span>
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
        <p class="card-description">Service availability.</p>
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
            <h3 class="recipe-title">Apps</h3>
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
            class="usx-btn usx-btn--secondary sync-btn"
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
          Synced events recorded in <code>~/Vault/Memory/Activity/Activity/events.jsonl</code> · View <code>~/Vault/Memory/Activity/Activity/Daily_Activity.md</code>
        </div>
      </div>
      <div v-else class="activity-empty">
        <p>No activity events synced yet. Click "Sync Activity" to ingest local events into ~/Vault/Memory/Activity/Activity/.</p>
      </div>
    </div>
  </div>

  <div v-else class="server-loading">
    <span class="material-symbols-outlined spinning">progress_activity</span>
    <span>Loading service status…</span>
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
      syncMessage.value = "Apple Activity synchronized cleanly into ~/Vault/Memory/Activity/Activity/Daily_Activity.md (user notes preserved).";
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
  color: var(--usx-color-on-surface-variant, var(--usx-color-on-surface-muted));
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
  border-bottom: 1px solid var(--usx-color-outline-variant, color-mix(in srgb, var(--usx-color-on-surface) 10%, transparent));
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
  color: var(--usx-color-primary, var(--usx-color-primary));
}

.recipe-title {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--usx-color-on-surface, var(--usx-color-on-surface));
}

.recipe-desc {
  margin: 0.25rem 0 0;
  font-size: 0.85rem;
  color: var(--usx-color-on-surface-variant, var(--usx-color-on-surface-muted));
}

.header-meta {
  display: flex;
  gap: 0.5rem;
}

.recipe-badge {
  font-size: 0.75rem;
  padding: 0.25rem 0.6rem;
  background: var(--usx-color-surface-container, color-mix(in srgb, var(--usx-color-on-surface) 6%, transparent));
  border-radius: 4px;
  color: var(--usx-color-on-surface-variant, var(--usx-color-on-surface-muted));
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
  background: var(--usx-color-surface-container, color-mix(in srgb, var(--usx-color-on-surface) 4%, transparent));
  border: 1px solid var(--usx-color-outline-variant, color-mix(in srgb, var(--usx-color-on-surface) 8%, transparent));
  transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;
}

.matrix-card:hover {
  background: var(--usx-color-surface-container-high, color-mix(in srgb, var(--usx-color-on-surface) 7%, transparent));
  border-color: var(--usx-color-outline, color-mix(in srgb, var(--usx-color-on-surface) 20%, transparent));
  transform: translateY(-2px);
  box-shadow: 0 4px 12px color-mix(in srgb, var(--usx-color-scrim) 25%, transparent);
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
  background: color-mix(in srgb, var(--usx-color-primary) 12%, transparent);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--usx-color-primary, var(--usx-color-primary));
}

.icon-avatar .material-symbols-outlined {
  font-size: 20px;
}

.icon-avatar--success {
  background: color-mix(in srgb, var(--usx-color-success) 12%, transparent);
  color: var(--usx-color-success);
}

.icon-avatar--warning {
  background: color-mix(in srgb, var(--usx-color-warning) 12%, transparent);
  color: var(--usx-color-warning);
}

.icon-avatar--danger {
  background: color-mix(in srgb, var(--usx-color-danger) 12%, transparent);
  color: var(--usx-color-danger);
}

.card-tag {
  font-size: 0.7rem;
  padding: 0.2rem 0.5rem;
  border-radius: 12px;
  background: color-mix(in srgb, var(--usx-color-on-surface) 6%, transparent);
  color: var(--usx-color-on-surface-variant, var(--usx-color-on-surface-muted));
  font-weight: 500;
}

.card-tag--success {
  background: color-mix(in srgb, var(--usx-color-success) 12%, transparent);
  color: var(--usx-color-success);
}

.card-tag--warning {
  background: color-mix(in srgb, var(--usx-color-warning) 12%, transparent);
  color: var(--usx-color-warning);
}

.card-tag--danger {
  background: color-mix(in srgb, var(--usx-color-danger) 12%, transparent);
  color: var(--usx-color-danger);
}

.card-title {
  margin: 0 0 0.35rem;
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--usx-color-on-surface, var(--usx-color-on-surface));
}

.card-description {
  margin: 0 0 1rem;
  font-size: 0.82rem;
  line-height: 1.4;
  color: var(--usx-color-on-surface-variant, var(--usx-color-on-surface-muted));
  flex: 1;
}

.card-footer {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  padding-top: 0.75rem;
  border-top: 1px solid var(--usx-color-outline-variant, color-mix(in srgb, var(--usx-color-on-surface) 6%, transparent));
}

.card-metric {
  font-size: 1.35rem;
  font-family: var(--usx-font-family-mono, monospace);
  font-weight: 700;
  color: var(--usx-color-on-surface, var(--usx-color-on-surface));
}

.card-metric-sub {
  font-size: 0.75rem;
  color: var(--usx-color-on-surface-variant, var(--usx-color-on-surface-muted));
}

.metric--success { color: var(--usx-color-success); }
.metric--warning { color: var(--usx-color-warning); }
.metric--danger { color: var(--usx-color-danger); }

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
  background: var(--usx-color-surface-container, color-mix(in srgb, var(--usx-color-on-surface) 3%, transparent));
  border: 1px solid var(--usx-color-outline-variant, color-mix(in srgb, var(--usx-color-on-surface) 8%, transparent));
  transition: background 0.15s ease, border-color 0.15s ease;
}

.task-item-card:hover {
  background: var(--usx-color-surface-container-high, color-mix(in srgb, var(--usx-color-on-surface) 6%, transparent));
  border-color: var(--usx-color-outline, color-mix(in srgb, var(--usx-color-on-surface) 18%, transparent));
}

.task-item-icon-col {
  padding-top: 2px;
}

.status-icon {
  font-size: 20px;
}

.icon-done { color: var(--usx-color-success); }
.icon-progress {
  color: var(--usx-color-primary);
  animation: spin 3s linear infinite;
}
.icon-fail { color: var(--usx-color-danger); }

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
  color: var(--usx-color-on-surface, var(--usx-color-on-surface));
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
  background: color-mix(in srgb, var(--usx-color-success) 15%, transparent);
  color: var(--usx-color-success);
}

.badge--degraded {
  background: color-mix(in srgb, var(--usx-color-warning) 15%, transparent);
  color: var(--usx-color-warning);
}

.badge--down {
  background: color-mix(in srgb, var(--usx-color-danger) 15%, transparent);
  color: var(--usx-color-danger);
}

.task-subtitle {
  margin: 0.25rem 0 0.5rem;
  font-size: 0.82rem;
  color: var(--usx-color-on-surface-variant, var(--usx-color-on-surface-muted));
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
  background: color-mix(in srgb, var(--usx-color-on-surface) 5%, transparent);
  color: var(--usx-color-on-surface-variant, var(--usx-color-on-surface-muted));
  font-family: var(--usx-font-family-mono, monospace);
  font-size: 0.72rem;
}

.task-timestamp {
  color: var(--usx-color-on-surface-variant, var(--usx-color-on-surface-muted));
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
  background: var(--usx-color-surface-container, color-mix(in srgb, var(--usx-color-on-surface) 3%, transparent));
  border: 1px solid var(--usx-color-outline-variant, color-mix(in srgb, var(--usx-color-on-surface) 8%, transparent));
  border-radius: 8px;
  transition: all 0.15s ease;
}

.launcher-card:hover {
  background: var(--usx-color-surface-container-high, color-mix(in srgb, var(--usx-color-on-surface) 6%, transparent));
  border-color: var(--usx-color-primary, var(--usx-color-primary));
}

.launcher-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 6px;
  background: color-mix(in srgb, var(--usx-color-primary) 12%, transparent);
  color: var(--usx-color-primary, var(--usx-color-primary));
}

.launcher-info {
  flex: 1;
  min-width: 0;
}

.launcher-name {
  font-weight: 500;
  font-size: 0.88rem;
  color: var(--usx-color-on-surface, var(--usx-color-on-surface));
}

.launcher-desc {
  font-size: 0.75rem;
  color: var(--usx-color-on-surface-variant, var(--usx-color-on-surface-muted));
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.launcher-badge {
  font-size: 0.68rem;
  text-transform: uppercase;
  padding: 0.15rem 0.4rem;
  border-radius: 4px;
  background: color-mix(in srgb, var(--usx-color-on-surface) 5%, transparent);
  color: var(--usx-color-on-surface-variant, var(--usx-color-on-surface-muted));
}

/* ── Activity Feed ── */
.sync-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.35rem 0.75rem;
  background: var(--usx-color-primary, var(--usx-color-primary));
  color: var(--usx-color-background);
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
  background: color-mix(in srgb, var(--usx-color-success) 12%, transparent);
  border: 1px solid color-mix(in srgb, var(--usx-color-success) 30%, transparent);
  color: var(--usx-color-success);
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
  background: var(--usx-color-surface-container, color-mix(in srgb, var(--usx-color-on-surface) 3%, transparent));
  border: 1px solid var(--usx-color-outline-variant, color-mix(in srgb, var(--usx-color-on-surface) 6%, transparent));
  border-radius: 6px;
}

.activity-tag {
  font-size: 0.7rem;
  text-transform: uppercase;
  font-weight: 600;
  padding: 0.15rem 0.45rem;
  border-radius: 4px;
}

.activity-tag--calendar { background: color-mix(in srgb, var(--usx-color-info) 15%, transparent); color: var(--usx-color-info); }
.activity-tag--reminders { background: color-mix(in srgb, var(--usx-color-warning) 15%, transparent); color: var(--usx-color-warning); }
.activity-tag--mail { background: color-mix(in srgb, var(--usx-color-accent) 15%, transparent); color: var(--usx-color-accent); }
.activity-tag--notes { background: color-mix(in srgb, var(--usx-color-success) 15%, transparent); color: var(--usx-color-success); }

.activity-details {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.85rem;
}

.activity-time {
  font-size: 0.75rem;
  color: var(--usx-color-on-surface-variant, var(--usx-color-on-surface-muted));
}

.activity-footer-note {
  font-size: 0.75rem;
  color: var(--usx-color-on-surface-variant, var(--usx-color-on-surface-muted));
  padding: 0.5rem 0;
  font-style: italic;
}

.activity-empty {
  padding: 1.5rem 0;
  text-align: center;
  color: var(--usx-color-on-surface-variant, var(--usx-color-on-surface-muted));
  font-size: 0.85rem;
}
</style>

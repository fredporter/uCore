<template>
  <div class="services-panel-shell">
    <!-- Header -->
    <div class="recipe-header">
      <div class="header-left">
        <span class="material-symbols-outlined header-icon">miscellaneous_services</span>
        <div>
          <h2 class="recipe-title">Unified Services &amp; Tools</h2>
          <p class="recipe-desc">
            {{ srv.unifiedServices.length }} registered ({{ kindCount("service") }} services &middot; {{ kindCount("tool") }} tools &middot; {{ kindCount("mcp") }} MCP)
          </p>
        </div>
      </div>
      <div class="header-meta">
        <button class="m3-button" @click="handleRefresh">
          <span class="material-symbols-outlined">refresh</span>
          <span>Refresh</span>
        </button>
      </div>
    </div>

    <!-- Crash recovery banner via USX Callout Caution -->
    <div v-if="downServices.length > 0" class="usx-callout usx-callout-caution">
      <div class="usx-callout-header">
        <span class="material-symbols-outlined">bug_report</span>
        <span>{{ downServices.length }} Service{{ downServices.length > 1 ? "s" : "" }} Not Responding</span>
      </div>
      <div class="crash-banner-content">
        <span>Restart managed runtimes below or open diagnostics for recovery guidance.</span>
        <button class="m3-button m3-button-danger" @click="$router.push('/system/s500')">
          <span class="material-symbols-outlined">medical_services</span>
          <span>Open Crash Recovery</span>
        </button>
      </div>
    </div>

    <!-- Unified Services Table in USX Container Card -->
    <div class="table-container-card">
      <div v-if="srv.unifiedServices.length === 0" class="server-empty-state">
        <span class="material-symbols-outlined empty-icon">dns</span>
        <p>No services registered or discovered.</p>
      </div>
      <div v-else class="server-table-wrap">
        <table class="usx-table">
          <thead>
            <tr>
              <th>Service</th>
              <th>Kind</th>
              <th>Description</th>
              <th>Detail</th>
              <th>Status</th>
              <th v-if="downServices.length > 0">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="svc in srv.unifiedServices" :key="svc.id">
              <td>
                <span class="server-service-name-cell">
                  <span class="service-table-icon">
                    <span class="material-symbols-outlined">{{ serviceIcon(svc) }}</span>
                  </span>
                  <span class="service-name-text">{{ svc.name }}</span>
                </span>
              </td>
              <td>
                <span class="kind-pill" :class="`kind-pill--${svc.kind}`">{{ svc.kind }}</span>
              </td>
              <td class="server-desc-cell">{{ svc.description }}</td>
              <td class="server-mono-cell">{{ serviceDetail(svc) }}</td>
              <td>
                <span
                  class="status-pill"
                  :class="`status-pill--${svc.status}`"
                >
                  {{ svc.status }}
                </span>
              </td>
              <td v-if="downServices.length > 0">
                <div v-if="svc.status !== 'up' && svc.actions.includes('restart')" class="crash-inline-actions">
                  <button
                    class="crash-btn"
                    title="Restart service"
                    :disabled="actionLoading === svc.name"
                    @click="doRestart(svc.name)"
                  >
                    <span class="material-symbols-outlined">restart_alt</span>
                  </button>
                </div>
                <span v-else class="server-mono-cell">{{ svc.status === 'up' ? '—' : 'Manual recovery' }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Host-Native Integrations (Zen Host / Apple Events) - USX Card Matrix -->
    <div class="host-integrations-section">
      <div class="recipe-header">
        <div class="header-left">
          <span class="material-symbols-outlined header-icon">laptop_mac</span>
          <div>
            <h3 class="recipe-title">Host-Native Integrations</h3>
            <p class="recipe-desc">
              Level 1 of the Zen reuse hierarchy: Native Apple Events &amp; osascript bridge without heavyweight wrappers.
            </p>
          </div>
        </div>
        <div class="header-actions">
          <button
            class="m3-button"
            :disabled="actionLoading === 'notify'"
            @click="testNotification"
          >
            <span class="material-symbols-outlined">notifications</span>
            <span>Test Toast</span>
          </button>
          <button
            class="m3-button"
            :disabled="actionLoading === 'say'"
            @click="testSpeech"
          >
            <span class="material-symbols-outlined">volume_up</span>
            <span>Test Speech</span>
          </button>
          <button
            class="m3-button"
            :disabled="actionLoading === 'reminders'"
            @click="testFetchReminders"
          >
            <span class="material-symbols-outlined">checklist</span>
            <span>Fetch Reminders</span>
          </button>
          <button
            class="m3-button"
            :disabled="actionLoading === 'notes'"
            @click="testFetchNotes"
          >
            <span class="material-symbols-outlined">description</span>
            <span>Fetch Notes</span>
          </button>
        </div>
      </div>

      <div class="matrix-grid">
        <!-- Safari Tab Intake -->
        <div class="matrix-card">
          <div class="card-top-row">
            <div class="icon-avatar">
              <span class="material-symbols-outlined">open_in_browser</span>
            </div>
            <span class="card-tag">Browser</span>
          </div>
          <h4 class="card-title">Safari Tab Intake</h4>
          <p class="card-description">Extract active tab URLs, titles, and text contents via Apple Events.</p>
          <div class="card-footer">
            <span
              class="status-pill"
              :class="hostCaps?.capabilities?.browser_intake ? 'status-pill--up' : 'status-pill--neutral'"
            >
              {{ hostCaps?.capabilities?.browser_intake ? "Available" : "Unavailable" }}
            </span>
            <span class="card-subtext">Apple Events</span>
          </div>
        </div>

        <!-- Apple Notes Export -->
        <div class="matrix-card">
          <div class="card-top-row">
            <div class="icon-avatar">
              <span class="material-symbols-outlined">note_alt</span>
            </div>
            <span class="card-tag">Notes</span>
          </div>
          <h4 class="card-title">Apple Notes Export</h4>
          <p class="card-description">Export research briefs and notes directly to the macOS Notes application.</p>
          <div class="card-footer">
            <span
              class="status-pill"
              :class="hostCaps?.capabilities?.notes_export ? 'status-pill--up' : 'status-pill--neutral'"
            >
              {{ hostCaps?.capabilities?.notes_export ? "Available" : "Unavailable" }}
            </span>
            <span class="card-subtext">ScriptingBridge</span>
          </div>
        </div>

        <!-- Apple Notes Intake -->
        <div class="matrix-card">
          <div class="card-top-row">
            <div class="icon-avatar">
              <span class="material-symbols-outlined">description</span>
            </div>
            <span class="card-tag">Notes</span>
          </div>
          <h4 class="card-title">Apple Notes Intake</h4>
          <p class="card-description">Ingest personal notes into uKnowledge citation provenance store.</p>
          <div class="card-footer">
            <span
              class="status-pill"
              :class="hostCaps?.capabilities?.notes_intake ? 'status-pill--up' : 'status-pill--neutral'"
            >
              {{ hostCaps?.capabilities?.notes_intake ? "Available" : "Unavailable" }}
            </span>
            <span class="card-subtext">Local Intake</span>
          </div>
        </div>

        <!-- Apple Reminders Sync -->
        <div class="matrix-card">
          <div class="card-top-row">
            <div class="icon-avatar">
              <span class="material-symbols-outlined">task_alt</span>
            </div>
            <span class="card-tag">Reminders</span>
          </div>
          <h4 class="card-title">Apple Reminders Sync</h4>
          <p class="card-description">Write workflow tasks and reminders directly to Apple Reminders.</p>
          <div class="card-footer">
            <span
              class="status-pill"
              :class="hostCaps?.capabilities?.reminders_export ? 'status-pill--up' : 'status-pill--neutral'"
            >
              {{ hostCaps?.capabilities?.reminders_export ? "Available" : "Unavailable" }}
            </span>
            <span class="card-subtext">EventKit</span>
          </div>
        </div>

        <!-- Apple Reminders Intake -->
        <div class="matrix-card">
          <div class="card-top-row">
            <div class="icon-avatar">
              <span class="material-symbols-outlined">checklist</span>
            </div>
            <span class="card-tag">Reminders</span>
          </div>
          <h4 class="card-title">Apple Reminders Intake</h4>
          <p class="card-description">Incorporate active Reminders lists into the daily briefing spool.</p>
          <div class="card-footer">
            <span
              class="status-pill"
              :class="hostCaps?.capabilities?.reminders_intake ? 'status-pill--up' : 'status-pill--neutral'"
            >
              {{ hostCaps?.capabilities?.reminders_intake ? "Available" : "Unavailable" }}
            </span>
            <span class="card-subtext">PIM Feed</span>
          </div>
        </div>

        <!-- Desktop Notifications -->
        <div class="matrix-card">
          <div class="card-top-row">
            <div class="icon-avatar">
              <span class="material-symbols-outlined">notifications</span>
            </div>
            <span class="card-tag">System</span>
          </div>
          <h4 class="card-title">Desktop Notifications</h4>
          <p class="card-description">Trigger native macOS Notification Center alerts without web notification prompts.</p>
          <div class="card-footer">
            <span
              class="status-pill"
              :class="hostCaps?.capabilities?.notifications ? 'status-pill--up' : 'status-pill--neutral'"
            >
              {{ hostCaps?.capabilities?.notifications ? "Available" : "Unavailable" }}
            </span>
            <span class="card-subtext">osascript</span>
          </div>
        </div>

        <!-- Host Speech -->
        <div class="matrix-card">
          <div class="card-top-row">
            <div class="icon-avatar">
              <span class="material-symbols-outlined">record_voice_over</span>
            </div>
            <span class="card-tag">Audio</span>
          </div>
          <h4 class="card-title">Host Speech (say)</h4>
          <p class="card-description">Zero-latency sovereign text-to-speech synthesis using macOS built-in voices.</p>
          <div class="card-footer">
            <span
              class="status-pill"
              :class="hostCaps?.capabilities?.speech_tts ? 'status-pill--up' : 'status-pill--neutral'"
            >
              {{ hostCaps?.capabilities?.speech_tts ? "Available" : "Unavailable" }}
            </span>
            <span class="card-subtext">/usr/bin/say</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useSnackbarOpsStore } from "../../../stores/snackbarOps";
import { useSnackbarStore } from "../../../stores/snackbar";
import UIcon from "../../../skills/atoms/UIcon.vue";
import UBadge from "../../../skills/atoms/UBadge.vue";
import UButton from "../../../skills/atoms/UButton.vue";
import {
  getHostCapabilities,
  intakeAppleNotes,
  intakeAppleReminders,
  sendHostNotification,
  sendHostSay,
  type HostCapabilitiesResult,
} from "../../browserui/ApiBridge";

const srv = useSnackbarOpsStore();
const toast = useSnackbarStore();

const actionLoading = ref<string | null>(null);

const downServices = computed(() =>
  srv.unifiedServices.filter((s) => s.status !== "up"),
);

async function doRestart(name: string) {
  actionLoading.value = name;
  const ok = await srv.restartService(name);
  toast.show(
    ok ? `Service "${name}" restarted` : `Failed to restart "${name}"`,
    ok ? "success" : "error",
    4000,
    "services",
  );
  actionLoading.value = null;
  srv.fetchUnifiedServices();
}

function kindCount(kind: string): number {
  return srv.unifiedServices.filter((s) => s.kind === kind).length;
}

function serviceIcon(svc: {
  kind: string;
  type: string;
  name: string;
}): string {
  if (svc.kind === "tool") {
    const map: Record<string, string> = {
      git: "code",
      docker: "deployed_code",
      node: "javascript",
      python: "terminal",
      ollama: "smart_toy",
      gh: "code",
    };
    return map[svc.name.toLowerCase()] || "build";
  }
  if (svc.kind === "mcp") return "dns";
  return svc.type === "system" ? "settings" : "dns";
}

function kindBadge(kind: string): "success" | "info" | "warning" {
  if (kind === "tool") return "success";
  if (kind === "mcp") return "warning";
  return "info";
}

function serviceDetail(svc: {
  kind: string;
  port: number;
  meta: Record<string, any>;
}): string {
  if (svc.kind === "tool") {
    const ver = svc.meta?.version || "";
    return ver ? `v${ver}` : "";
  }
  if (svc.kind === "mcp") {
    return svc.meta?.endpoint || "";
  }
  return svc.port ? `:${svc.port}` : "";
}

onMounted(() => {
  if (srv.agents.length === 0) {
    srv.fetchAgents();
  }
  if (srv.unifiedServices.length === 0) {
    srv.fetchUnifiedServices();
  }
  loadHostCapabilities();
});

const hostCaps = ref<HostCapabilitiesResult | null>(null);

async function loadHostCapabilities() {
  try {
    hostCaps.value = await getHostCapabilities();
  } catch (err) {
    console.debug("Failed to load host capabilities", err);
  }
}

function handleRefresh() {
  srv.fetchUnifiedServices();
  loadHostCapabilities();
}

async function testNotification() {
  actionLoading.value = "notify";
  try {
    const res = await sendHostNotification(
      "uCore Zen",
      "Host native notification operational.",
      "Snackbar",
    );
    toast.show(
      res.ok ? "Desktop notification sent!" : "Notification failed",
      res.ok ? "success" : "error",
      3000,
      "services",
    );
  } catch (err: any) {
    toast.show(`Notification error: ${err?.message || err}`, "error", 3000, "services");
  } finally {
    actionLoading.value = null;
  }
}

async function testSpeech() {
  actionLoading.value = "say";
  try {
    const res = await sendHostSay("uDOS host integration nominal.");
    toast.show(
      res.ok ? "Speech synthesis triggered!" : "Speech synthesis failed",
      res.ok ? "success" : "error",
      3000,
      "services",
    );
  } catch (err: any) {
    toast.show(`Speech error: ${err?.message || err}`, "error", 3000, "services");
  } finally {
    actionLoading.value = null;
  }
}

async function testFetchReminders() {
  actionLoading.value = "reminders";
  try {
    const res = await intakeAppleReminders({ limit: 10 });
    if (res.ok) {
      toast.show(
        `Retrieved ${res.items.length} active Apple Reminders`,
        "success",
        4000,
        "services",
      );
    } else {
      toast.show(res.error || "Reminders intake failed", "warning", 4000, "services");
    }
  } catch (err: any) {
    toast.show(`Reminders intake error: ${err?.message || err}`, "error", 4000, "services");
  } finally {
    actionLoading.value = null;
  }
}

async function testFetchNotes() {
  actionLoading.value = "notes";
  try {
    const res = await intakeAppleNotes({ limit: 10 });
    if (res.ok) {
      toast.show(
        `Retrieved ${res.items.length} Apple Notes`,
        "success",
        4000,
        "services",
      );
    } else {
      toast.show(res.error || "Notes intake failed", "warning", 4000, "services");
    }
  } catch (err: any) {
    toast.show(`Notes intake error: ${err?.message || err}`, "error", 4000, "services");
  } finally {
    actionLoading.value = null;
  }
}
</script>

<style scoped>
@import '@udos/usx-tokens/usx-prose.css';

.services-panel-shell {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  width: 100%;
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

.header-meta,
.header-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

/* ── M3 Button Pattern ── */
.m3-button {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.4rem 0.75rem;
  font-size: 0.8rem;
  font-weight: 500;
  border-radius: 6px;
  border: 1px solid var(--usx-color-outline-variant, rgba(255, 255, 255, 0.15));
  background: var(--usx-color-surface-container, rgba(255, 255, 255, 0.04));
  color: var(--usx-color-on-surface, #e2e2e6);
  cursor: pointer;
  transition: all 0.15s ease;
}

.m3-button:hover:not(:disabled) {
  background: var(--usx-color-surface-container-high, rgba(255, 255, 255, 0.08));
  border-color: var(--usx-color-outline, rgba(255, 255, 255, 0.25));
}

.m3-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.m3-button .material-symbols-outlined {
  font-size: 18px;
}

.m3-button-danger {
  background: rgba(248, 81, 73, 0.15);
  border-color: rgba(248, 81, 73, 0.35);
  color: #f85149;
}

.m3-button-danger:hover:not(:disabled) {
  background: rgba(248, 81, 73, 0.25);
}

/* ── Callout Content ── */
.crash-banner-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
  margin-top: 0.25rem;
}

/* ── Table Container Card ── */
.table-container-card {
  border-radius: 12px;
  background: var(--usx-color-surface-container, rgba(255, 255, 255, 0.03));
  border: 1px solid var(--usx-color-outline-variant, rgba(255, 255, 255, 0.08));
  overflow: hidden;
}

.server-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  color: var(--usx-color-on-surface-variant, #8e9199);
}

.empty-icon {
  font-size: 36px;
  margin-bottom: 0.5rem;
  opacity: 0.5;
}

.server-table-wrap {
  overflow-x: auto;
}

.usx-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}

.usx-table th {
  text-align: left;
  font-weight: 600;
  color: var(--usx-color-on-surface-variant, #8e9199);
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--usx-color-outline-variant, rgba(255, 255, 255, 0.1));
  background: var(--usx-color-surface, #1e2025);
  white-space: nowrap;
}

.usx-table td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--usx-color-outline-variant, rgba(255, 255, 255, 0.05));
  vertical-align: middle;
}

.usx-table tr:hover {
  background: var(--usx-color-surface-container-high, rgba(255, 255, 255, 0.03));
}

.server-service-name-cell {
  display: inline-flex;
  align-items: center;
  gap: 0.65rem;
  font-weight: 500;
  color: var(--usx-color-on-surface, #e2e2e6);
}

.service-table-icon {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: rgba(168, 199, 250, 0.12);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--usx-color-primary, #a8c7fa);
}

.service-table-icon .material-symbols-outlined {
  font-size: 16px;
}

.service-name-text {
  font-size: 0.88rem;
  font-weight: 600;
}

.server-desc-cell {
  font-size: 0.82rem;
  color: var(--usx-color-on-surface-variant, #8e9199);
  max-width: 320px;
}

.server-mono-cell {
  font-family: var(--usx-font-family-mono, monospace);
  font-size: 0.78rem;
  color: var(--usx-color-on-surface-variant, #8e9199);
}

/* ── Pills and Badges ── */
.kind-pill {
  font-size: 0.68rem;
  text-transform: uppercase;
  font-weight: 600;
  padding: 0.15rem 0.45rem;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.06);
  color: var(--usx-color-on-surface-variant, #c4c6d0);
  font-family: var(--usx-font-family-mono, monospace);
}

.kind-pill--service {
  background: rgba(168, 199, 250, 0.12);
  color: #a8c7fa;
}

.kind-pill--tool {
  background: rgba(63, 185, 80, 0.12);
  color: #3fb950;
}

.kind-pill--mcp {
  background: rgba(210, 153, 34, 0.12);
  color: #d29922;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  font-size: 0.68rem;
  font-weight: 600;
  text-transform: uppercase;
  padding: 0.15rem 0.5rem;
  border-radius: 12px;
  letter-spacing: 0.03em;
}

.status-pill--up {
  background: rgba(63, 185, 80, 0.15);
  color: #3fb950;
}

.status-pill--degraded {
  background: rgba(210, 153, 34, 0.15);
  color: #d29922;
}

.status-pill--down {
  background: rgba(248, 81, 73, 0.15);
  color: #f85149;
}

.status-pill--neutral {
  background: rgba(255, 255, 255, 0.06);
  color: var(--usx-color-on-surface-variant, #8e9199);
}

.crash-inline-actions {
  display: flex;
  gap: 0.35rem;
}

.crash-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: 1px solid var(--usx-color-outline-variant, rgba(255, 255, 255, 0.15));
  border-radius: 6px;
  background: transparent;
  color: var(--usx-color-on-surface-variant, #8e9199);
  cursor: pointer;
  transition: all 0.15s ease;
}

.crash-btn:hover:not(:disabled) {
  color: #f85149;
  border-color: #f85149;
  background: rgba(248, 81, 73, 0.12);
}

.crash-btn .material-symbols-outlined {
  font-size: 16px;
}

/* ── Host-Native Integrations Section (USX Card Matrix) ── */
.host-integrations-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-top: 1rem;
}

.matrix-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 1rem;
  width: 100%;
}

.matrix-card {
  display: flex;
  flex-direction: column;
  padding: 1.15rem;
  border-radius: 12px;
  background: var(--usx-color-surface-container, rgba(255, 255, 255, 0.03));
  border: 1px solid var(--usx-color-outline-variant, rgba(255, 255, 255, 0.08));
  transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;
}

.matrix-card:hover {
  background: var(--usx-color-surface-container-high, rgba(255, 255, 255, 0.06));
  border-color: var(--usx-color-outline, rgba(255, 255, 255, 0.2));
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
}

.card-top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.65rem;
}

.icon-avatar {
  width: 36px;
  height: 36px;
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

.card-tag {
  font-size: 0.7rem;
  padding: 0.2rem 0.5rem;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.06);
  color: var(--usx-color-on-surface-variant, #c4c6d0);
  font-weight: 500;
}

.card-title {
  margin: 0 0 0.35rem;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--usx-color-on-surface, #e2e2e6);
}

.card-description {
  margin: 0 0 0.85rem;
  font-size: 0.8rem;
  line-height: 1.4;
  color: var(--usx-color-on-surface-variant, #9aa0a6);
  flex: 1;
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 0.65rem;
  border-top: 1px solid var(--usx-color-outline-variant, rgba(255, 255, 255, 0.06));
}

.card-subtext {
  font-size: 0.72rem;
  color: var(--usx-color-on-surface-variant, #8e9199);
  font-family: var(--usx-font-family-mono, monospace);
}
</style>

<template>
  <div>
    <div class="usx-flex-between usx-mb-md">
      <div>
        <h3 class="surface__panel-title">Services</h3>
        <p class="server-muted-text-sm">
          {{ srv.unifiedServices.length }} total ({{
            kindCount("service")
          }}
          services &middot; {{ kindCount("tool") }} tools &middot;
          {{ kindCount("mcp") }} MCP)
        </p>
      </div>
      <UButton
        variant="secondary"
        size="sm"
        icon="refresh"
        @click="handleRefresh"
        >Refresh</UButton
      >
    </div>

    <!-- Crash recovery banner -->
    <div v-if="downServices.length > 0" class="crash-banner">
      <UIcon name="bug_report" class="crash-banner-icon" />
      <div class="crash-banner-text">
        <strong
          >{{ downServices.length }} service{{
            downServices.length > 1 ? "s" : ""
          }}
          not responding.</strong
        >
        <span>Restart managed runtimes or open diagnostics for recovery guidance.</span>
      </div>
      <UButton
        variant="secondary"
        size="sm"
        icon="medical_services"
        class="crash-banner-btn"
        @click="$router.push('/system/s500')"
      >
        Open Crash Recovery
      </UButton>
    </div>

    <div v-if="srv.unifiedServices.length === 0" class="server-muted-text-sm">
      No services available.
    </div>
    <div v-else class="server-table-wrap">
      <table class="server-table">
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
                <UIcon :name="serviceIcon(svc)" />
                <span>{{ svc.name }}</span>
              </span>
            </td>
            <td>
              <UBadge :type="kindBadge(svc.kind)" size="sm">{{
                svc.kind
              }}</UBadge>
            </td>
            <td class="server-muted-text-sm">{{ svc.description }}</td>
            <td class="server-muted-text-sm">{{ serviceDetail(svc) }}</td>
            <td>
              <UBadge
                :type="
                  svc.status === 'up'
                    ? 'success'
                    : svc.status === 'degraded'
                      ? 'warning'
                      : 'error'
                "
                size="sm"
              >
                {{ svc.status }}
              </UBadge>
            </td>
            <td v-if="downServices.length > 0">
              <div v-if="svc.status !== 'up' && svc.actions.includes('restart')" class="crash-inline-actions">
                <button
                  class="crash-btn"
                  title="Restart service"
                  :disabled="actionLoading === svc.name"
                  @click="doRestart(svc.name)"
                >
                  <UIcon name="restart_alt" />
                </button>
              </div>
              <span v-else class="server-muted-text-sm">{{ svc.status === 'up' ? '—' : 'Manual recovery' }}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Host-Native Integrations (Zen Host / Apple Events) -->
    <div class="host-pim-card usx-mt-lg">
      <div class="usx-flex-between usx-mb-sm">
        <div class="host-pim-title">
          <UIcon name="laptop_mac" />
          <strong>Host-Native Integrations (Apple Events / Zen Host)</strong>
        </div>
        <div class="host-pim-actions">
          <UButton
            variant="ghost"
            size="sm"
            icon="notifications"
            :disabled="actionLoading === 'notify'"
            @click="testNotification"
          >
            Test Toast
          </UButton>
          <UButton
            variant="ghost"
            size="sm"
            icon="volume_up"
            :disabled="actionLoading === 'say'"
            @click="testSpeech"
          >
            Test Speech
          </UButton>
          <UButton
            variant="ghost"
            size="sm"
            icon="checklist"
            :disabled="actionLoading === 'reminders'"
            @click="testFetchReminders"
          >
            Fetch Reminders
          </UButton>
          <UButton
            variant="ghost"
            size="sm"
            icon="description"
            :disabled="actionLoading === 'notes'"
            @click="testFetchNotes"
          >
            Fetch Notes
          </UButton>
        </div>
      </div>
      <p class="server-muted-text-sm usx-mb-sm">
        Level 1 of the Zen reuse hierarchy: Native OS automation without heavyweight wrappers or background daemons.
      </p>

      <div class="host-pim-grid">
        <div class="host-pim-item">
          <div class="host-pim-item__header">
            <UIcon name="open_in_browser" />
            <span>Safari Tab Intake</span>
          </div>
          <UBadge :type="hostCaps?.capabilities?.browser_intake ? 'success' : 'neutral'" size="sm">
            {{ hostCaps?.capabilities?.browser_intake ? "Available" : "Unavailable" }}
          </UBadge>
        </div>

        <div class="host-pim-item">
          <div class="host-pim-item__header">
            <UIcon name="note_alt" />
            <span>Apple Notes Export</span>
          </div>
          <UBadge :type="hostCaps?.capabilities?.notes_export ? 'success' : 'neutral'" size="sm">
            {{ hostCaps?.capabilities?.notes_export ? "Available" : "Unavailable" }}
          </UBadge>
        </div>

        <div class="host-pim-item">
          <div class="host-pim-item__header">
            <UIcon name="description" />
            <span>Apple Notes Intake</span>
          </div>
          <UBadge :type="hostCaps?.capabilities?.notes_intake ? 'success' : 'neutral'" size="sm">
            {{ hostCaps?.capabilities?.notes_intake ? "Available" : "Unavailable" }}
          </UBadge>
        </div>

        <div class="host-pim-item">
          <div class="host-pim-item__header">
            <UIcon name="task_alt" />
            <span>Apple Reminders Sync</span>
          </div>
          <UBadge :type="hostCaps?.capabilities?.reminders_export ? 'success' : 'neutral'" size="sm">
            {{ hostCaps?.capabilities?.reminders_export ? "Available" : "Unavailable" }}
          </UBadge>
        </div>

        <div class="host-pim-item">
          <div class="host-pim-item__header">
            <UIcon name="checklist" />
            <span>Apple Reminders Intake</span>
          </div>
          <UBadge :type="hostCaps?.capabilities?.reminders_intake ? 'success' : 'neutral'" size="sm">
            {{ hostCaps?.capabilities?.reminders_intake ? "Available" : "Unavailable" }}
          </UBadge>
        </div>

        <div class="host-pim-item">
          <div class="host-pim-item__header">
            <UIcon name="notifications" />
            <span>Desktop Notifications</span>
          </div>
          <UBadge :type="hostCaps?.capabilities?.notifications ? 'success' : 'neutral'" size="sm">
            {{ hostCaps?.capabilities?.notifications ? "Available" : "Unavailable" }}
          </UBadge>
        </div>

        <div class="host-pim-item">
          <div class="host-pim-item__header">
            <UIcon name="record_voice_over" />
            <span>Host Speech (/usr/bin/say)</span>
          </div>
          <UBadge :type="hostCaps?.capabilities?.speech_tts ? 'success' : 'neutral'" size="sm">
            {{ hostCaps?.capabilities?.speech_tts ? "Available" : "Unavailable" }}
          </UBadge>
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
.server-muted-text-sm {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
}
.server-table-wrap {
  overflow-x: auto;
}
.server-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--usx-font-size-sm);
}
.server-table th {
  text-align: left;
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface-muted);
  padding: var(--usx-spacing-sm);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
  white-space: nowrap;
}
.server-table td {
  padding: var(--usx-spacing-sm);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
  vertical-align: middle;
}
.server-service-name-cell {
  display: inline-flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  font-weight: var(--usx-font-weight-semibold);
  min-width: 0;
  overflow-wrap: anywhere;
}
.server-subheading {
  font-size: var(--usx-font-size-base);
  margin-bottom: var(--usx-spacing-sm);
  color: var(--usx-color-on-surface);
}

/* ─── Crash recovery banner ──────────────────────────────────── */
.crash-banner {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-md);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border: var(--usx-border-width) solid
    color-mix(in srgb, var(--usx-color-danger) 40%, transparent);
  border-radius: var(--usx-radius-md);
  background: color-mix(in srgb, var(--usx-color-danger) 8%, transparent);
  margin-bottom: var(--usx-spacing-md);
}

.crash-banner-icon {
  color: var(--usx-color-danger);
  font-size: var(--usx-font-size-xl);
  flex-shrink: 0;
}

.crash-banner-text {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-base);
}

.crash-banner-text span {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
}

/* ─── Inline per-service actions ─────────────────────────────── */
.crash-inline-actions {
  display: flex;
  gap: var(--usx-spacing-xs);
}

.crash-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: var(--usx-spacing-xl);
  height: var(--usx-spacing-xl);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface-muted);
  cursor: pointer;
  transition:
    color var(--usx-transition-fast),
    border-color var(--usx-transition-fast),
    background var(--usx-transition-fast);
}

.crash-btn:hover:not(:disabled) {
  color: var(--usx-color-primary);
  border-color: var(--usx-color-primary);
  background: color-mix(in srgb, var(--usx-color-primary) 8%, transparent);
}

.crash-btn--danger:hover:not(:disabled) {
  color: var(--usx-color-danger);
  border-color: var(--usx-color-danger);
  background: color-mix(in srgb, var(--usx-color-danger) 8%, transparent);
}

.crash-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.crash-banner-btn {
  flex-shrink: 0;
}

/* ─── Host-Native PIM Card ─────────────────────────────────────────── */
.host-pim-card {
  padding: var(--usx-spacing-md);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  background: var(--usx-color-surface);
}

.host-pim-title {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  color: var(--usx-color-primary);
  font-size: var(--usx-font-size-base);
}

.host-pim-actions {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
}

.host-pim-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--usx-spacing-sm);
  margin-top: var(--usx-spacing-sm);
}

.host-pim-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--usx-spacing-sm);
  background: var(--usx-color-surface-variant);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
}

.host-pim-item__header {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  font-size: var(--usx-font-size-xs);
  font-weight: var(--usx-font-weight-medium);
  color: var(--usx-color-on-surface);
}
</style>

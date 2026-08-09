<template>
  <div
    class="surface"
    :class="{
      'surface--tab-nav-vertical': shell.tabOrientation === 'vertical',
    }"
  >
    <SurfaceTabNav
      v-model="activeTab"
      :tabs="SYSTEM_TABS"
      :orientation="shell.tabOrientation"
      @toggle-orientation="shell.toggleTabOrientation()"
    />
    <div class="surface__content">
      <!-- Pages Browser -->
      <div v-if="currentTab === 'pages'" class="system-panel system-tab-shell">
        <h3 class="surface__panel-title">System Pages</h3>
        <p class="system-muted-copy">Browse S-pages.</p>

        <div class="system-readiness surface__panel">
          <div class="system-readiness-head">
            <h4 class="system-section-title">Capability Readiness</h4>
            <UBadge v-if="readinessLoading" type="info" size="sm"
              >checking</UBadge
            >
            <UBadge
              v-else-if="readinessBlockedCount > 0"
              type="warning"
              size="sm"
              >repair required</UBadge
            >
            <UBadge v-else type="info" size="sm">ready</UBadge>
          </div>

          <p class="system-muted-copy" v-if="readinessLoading">
            Running startup preflight snapshot...
          </p>
          <p class="system-muted-copy" v-else-if="readinessError">
            {{ readinessError }}
          </p>

          <div v-else-if="readinessSnapshot" class="system-readiness-summary">
            <span>Checked: {{ readinessSnapshot.count }}</span>
            <span>Blocked: {{ readinessBlockedCount }}</span>
          </div>

          <ul
            v-if="!readinessLoading && blockedCapabilities.length > 0"
            class="system-readiness-list"
          >
            <li
              v-for="cap in blockedCapabilities.slice(0, 4)"
              :key="cap.capability"
              class="system-readiness-item"
            >
              <span class="system-readiness-cap">{{ cap.capability }}</span>
              <span class="system-readiness-action">
                {{
                  cap.repair?.[0]?.action ||
                  "Complete repair steps and re-check."
                }}
              </span>
            </li>
          </ul>

          <button class="system-action-btn" @click="fetchReadiness">
            Re-check readiness
          </button>
        </div>

        <div class="system-pages-grid">
          <div
            v-for="page in allPages"
            :key="page.id"
            class="system-page-card"
            @click="navigateToPage(page.id)"
          >
            <UIcon :name="page.icon" />
            <span class="system-page-id">{{ page.id }}</span>
            <span class="system-page-title">{{ page.title }}</span>
          </div>
        </div>
        <p v-if="allPages.length === 0" class="system-muted-copy">
          No pages found.
        </p>

        <div class="system-runtime-redirect surface__panel">
          <h4 class="system-section-title">Runtime Operations</h4>
          <p class="system-muted-copy">
            Live runtime diagnostics have moved to Snackbar.
          </p>
          <div class="system-runtime-actions">
            <button
              class="system-action-btn"
              @click="goTo('/snackbar?tab=dashboard')"
            >
              Open Snackbar Dashboard
            </button>
            <button
              class="system-action-btn"
              @click="goTo('/snackbar?tab=services')"
            >
              Open Snackbar Services
            </button>
            <button
              class="system-action-btn"
              @click="goTo('/snackbar?tab=snacks')"
            >
              Open Snackbar Snacks
            </button>
          </div>
        </div>
      </div>

      <!-- Variables -->
      <div
        v-else-if="currentTab === 'variables'"
        class="system-panel system-tab-shell"
      >
        <h3 class="surface__panel-title">Variables</h3>
        <p class="system-muted-copy">User and installation variables.</p>
        <div v-if="loadingVars" class="system-loading">
          Loading variables...
        </div>
        <div v-else>
          <h4 class="system-section-title">User Variables</h4>
          <div class="system-table-wrap">
            <table class="system-table">
              <thead>
                <tr>
                  <th>Key</th>
                  <th>Value</th>
                  <th>Scope</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(value, key) in userVariables" :key="key">
                  <td>
                    <code class="system-var-key">{{ key }}</code>
                  </td>
                  <td>
                    <input
                      v-if="editingVar === key"
                      v-model="editVarValue"
                      class="system-var-input"
                      @keyup.enter="saveVariable(key)"
                      @keyup.escape="editingVar = null"
                    />
                    <span v-else class="system-var-value">{{ value }}</span>
                  </td>
                  <td><UBadge type="info" size="sm">user</UBadge></td>
                  <td>
                    <button
                      v-if="editingVar !== key"
                      class="system-edit-btn"
                      @click="startEditVar(key, value)"
                    >
                      Edit
                    </button>
                    <button
                      v-else
                      class="system-save-btn"
                      @click="saveVariable(key)"
                    >
                      Save
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <h4 class="system-section-title">Installation Metadata</h4>
          <div class="system-table-wrap">
            <table class="system-table">
              <thead>
                <tr>
                  <th>Key</th>
                  <th>Value</th>
                  <th>Scope</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(value, key) in installVariables" :key="key">
                  <td>
                    <code class="system-var-key">{{ key }}</code>
                  </td>
                  <td>
                    <span class="system-var-value">{{ value }}</span>
                  </td>
                  <td><UBadge type="neutral" size="sm">install</UBadge></td>
                </tr>
              </tbody>
            </table>
          </div>

          <h4 class="system-section-title">Models (Config)</h4>
          <p class="system-muted-copy">
            Provider / model configuration treated as variables.
          </p>
          <div v-if="modelsProviders.length === 0" class="system-muted-copy">
            No models configured.
          </div>
          <div v-else class="system-table-wrap">
            <table class="system-table">
              <thead>
                <tr>
                  <th>Provider</th>
                  <th>Name</th>
                  <th>Models</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="prov in modelsProviders" :key="prov.id">
                  <td>
                    <code class="system-var-key">{{ prov.id }}</code>
                  </td>
                  <td class="system-var-value">{{ prov.name }}</td>
                  <td>
                    <span class="system-var-value">
                      {{ (prov.models || []).join(", ") }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <h4 class="system-section-title">Agents (Config)</h4>
          <p class="system-muted-copy">
            Agent definitions are configuration (provider + model +
            capabilities).
          </p>
          <div v-if="agentConfigs.length === 0" class="system-muted-copy">
            No agent configs.
          </div>
          <div v-else class="system-table-wrap">
            <table class="system-table">
              <thead>
                <tr>
                  <th>Agent</th>
                  <th>Provider</th>
                  <th>Model</th>
                  <th>Capabilities</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="agent in agentConfigs" :key="agent.id">
                  <td>
                    <code class="system-var-key">{{ agent.name }}</code>
                  </td>
                  <td class="system-var-value">{{ agent.provider }}</td>
                  <td class="system-var-value">{{ agent.model || "—" }}</td>
                  <td>
                    <span class="system-var-value">
                      {{ (agent.capabilities || []).join(", ") }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Secrets -->
      <div
        v-else-if="currentTab === 'secrets'"
        class="system-panel system-tab-shell"
      >
        <h3 class="surface__panel-title">Secrets</h3>
        <p class="system-muted-copy">
          Encrypted secret storage. Values are masked by default.
        </p>
        <div class="system-secrets-actions">
          <button class="system-action-btn" @click="showAddSecret = true">
            + Add Secret
          </button>
          <button class="system-action-btn" @click="importSecretsFromEnv">
            ↳ Import from Env
          </button>
        </div>
        <div v-if="showAddSecret" class="system-add-secret-form">
          <input
            v-model="newSecretKey"
            placeholder="SECRET_NAME"
            class="system-var-input"
          />
          <input
            v-model="newSecretValue"
            placeholder="secret value"
            type="password"
            class="system-var-input"
          />
          <button class="system-save-btn" @click="addSecret">Save</button>
          <button class="system-edit-btn" @click="showAddSecret = false">
            Cancel
          </button>
        </div>
        <div v-if="loadingSecrets" class="system-loading">
          Loading secrets...
        </div>
        <div v-else class="system-table-wrap">
          <table class="system-table">
            <thead>
              <tr>
                <th>Key</th>
                <th>Value</th>
                <th>Scope</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="secret in secrets" :key="secret.key">
                <td>
                  <span class="system-secret-key">{{ secret.key }}</span>
                </td>
                <td>
                  <span class="system-secret-value">{{
                    revealingSecret === secret.key ? secret.value : "••••••••"
                  }}</span>
                </td>
                <td>
                  <UBadge type="info" size="sm">{{ secret.scope }}</UBadge>
                </td>
                <td class="system-secret-actions">
                  <button
                    class="system-edit-btn"
                    @click="toggleRevealSecret(secret.key)"
                  >
                    Reveal
                  </button>
                  <button
                    class="system-delete-btn"
                    @click="deleteSecret(secret.key)"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Global Settings -->
      <div
        v-else-if="currentTab === 'global-settings'"
        class="system-panel system-tab-shell"
      >
        <h3 class="surface__panel-title">Global Settings</h3>
        <p class="system-muted-copy">
          Theme, palette, and typography controls. Saved server-side.
        </p>
        <div class="system-settings-form">
          <div class="settings-row">
            <label>Theme</label
            ><select v-model="themeSettings.theme">
              <option>dark</option>
              <option>light</option>
              <option>auto</option>
            </select>
          </div>
          <div class="settings-row">
            <label>Font Size</label
            ><input
              type="range"
              min="12"
              max="24"
              v-model.number="themeSettings.fontSize"
            /><span>{{ themeSettings.fontSize }}px</span>
          </div>
          <div class="settings-row">
            <label>Palette</label
            ><select v-model="themeSettings.palette">
              <option>default</option>
              <option>ocean</option>
              <option>forest</option>
              <option>sunset</option>
            </select>
          </div>
        </div>
        <button
          class="system-action-btn system-save-settings-btn"
          @click="saveGlobalSettings"
        >
          Save Global Settings
        </button>
      </div>

      <!-- User Settings -->
      <div
        v-else-if="currentTab === 'user-settings'"
        class="system-panel system-tab-shell"
      >
        <h3 class="surface__panel-title">User Settings</h3>
        <p class="system-muted-copy">
          Your profile and preferences. Saved server-side.
        </p>
        <div class="system-settings-form">
          <div class="settings-row">
            <label>Display Name</label
            ><input type="text" v-model="userSettings.displayName" />
          </div>
          <div class="settings-row">
            <label>Email</label
            ><input
              type="email"
              v-model="userSettings.email"
              placeholder="user@example.com"
            />
          </div>
          <div class="settings-row">
            <label>Default Model</label
            ><select v-model="userSettings.defaultModel">
              <option>Llama 3.2</option>
              <option>GPT-4o</option>
              <option>DeepSeek V3</option>
            </select>
          </div>
        </div>
        <button
          class="system-action-btn system-save-settings-btn"
          @click="saveUserSettings"
        >
          Save User Settings
        </button>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import type { TabDef } from "../../skills/molecules/SurfaceTabNav.vue";

export const SYSTEM_TABS: TabDef[] = [
  { id: "pages", label: "Pages", icon: "dashboard" },
  { id: "variables", label: "Variables", icon: "tune" },
  { id: "secrets", label: "Secrets", icon: "key" },
  { id: "global-settings", label: "Global", icon: "settings" },
  { id: "user-settings", label: "User", icon: "person" },
];
</script>

<script setup lang="ts">
import { computed, ref, reactive, watch, onMounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useShellStore } from "../../stores/shell";
import { SNACKBAR_BASE } from "../../api/base";
import {
  getCapabilitiesReadiness,
  type CapabilityReadinessSnapshot,
  type CapabilityPreflightResult,
} from "../../api/preflight";
import UIcon from "../../skills/atoms/UIcon.vue";
import UBadge from "../../skills/atoms/UBadge.vue";
import SurfaceTabNav from "../../skills/molecules/SurfaceTabNav.vue";

const API_BASE = SNACKBAR_BASE;
const route = useRoute();
const router = useRouter();
const shell = useShellStore();
const VALID_SYSTEM_TABS = new Set(SYSTEM_TABS.map((tab) => tab.id));

const routeTab = String(route.query.tab || "");
const activeTab = ref(VALID_SYSTEM_TABS.has(routeTab) ? routeTab : "pages");
const currentTab = computed(() => activeTab.value);

// ── Pages ────────────────────────────────────────────────────────
const LOCAL_FALLBACK_PAGES = [
  { id: "S100", title: "Page Not Found", icon: "search_off" },
  { id: "S101", title: "Server Offline", icon: "cloud_off" },
  { id: "S300", title: "Internal Server Error", icon: "error" },
  { id: "S310", title: "Clipboard Full History", icon: "content_paste" },
  { id: "S320", title: "Access Restricted", icon: "lock" },
  { id: "S330", title: "Configuration Missing", icon: "settings" },
  { id: "S340", title: "Dependency Unavailable", icon: "link_off" },
  { id: "S500", title: "Service Crash Recovery", icon: "bug_report" },
  { id: "S600", title: "Help and Recovery", icon: "help" },
];
const allPages = ref<Array<{ id: string; title: string; icon: string }>>([]);
const readinessSnapshot = ref<CapabilityReadinessSnapshot | null>(null);
const readinessLoading = ref(false);
const readinessError = ref("");

const blockedCapabilities = computed<CapabilityPreflightResult[]>(() => {
  return (readinessSnapshot.value?.capabilities || []).filter(
    (cap) => !cap.ready,
  );
});

const readinessBlockedCount = computed(() => blockedCapabilities.value.length);

function navigateToPage(pageId: string) {
  router.push(`/system/${pageId.toLowerCase()}`);
}

function goTo(path: string) {
  router.push(path);
}

// ── Variables ────────────────────────────────────────────────────
const loadingVars = ref(true);
const userVariables = ref<Record<string, string>>({});
const installVariables = ref<Record<string, string>>({});
const editingVar = ref<string | null>(null);
const editVarValue = ref("");
const modelsProviders = ref<
  Array<{ id: string; name: string; models: string[] }>
>([]);
const agentConfigs = ref<
  Array<{
    id: string;
    name: string;
    provider: string;
    model: string;
    capabilities: string[];
  }>
>([]);

function startEditVar(key: string, value: string) {
  editingVar.value = key;
  editVarValue.value = value;
}

async function saveVariable(key: string) {
  try {
    const res = await fetch(`${API_BASE}/api/variables/user`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ [key]: editVarValue.value }),
    });
    if (res.ok) {
      userVariables.value[key] = editVarValue.value;
    }
  } catch {}
  editingVar.value = null;
}

// ── Secrets ──────────────────────────────────────────────────────
interface SecretItem {
  key: string;
  scope: string;
  value: string;
}
const secrets = ref<SecretItem[]>([]);
const loadingSecrets = ref(true);
const revealingSecret = ref<string | null>(null);
const showAddSecret = ref(false);
const newSecretKey = ref("");
const newSecretValue = ref("");

function toggleRevealSecret(key: string) {
  if (revealingSecret.value === key) {
    revealingSecret.value = null;
  } else {
    revealingSecret.value = key;
  }
}

async function addSecret() {
  const key = newSecretKey.value.trim();
  const value = newSecretValue.value.trim();
  if (!key || !value) return;
  try {
    const res = await fetch(`${API_BASE}/api/secrets/${key}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ value }),
    });
    if (res.ok) {
      secrets.value.push({ key, scope: "user", value: "••••••••" });
      newSecretKey.value = "";
      newSecretValue.value = "";
      showAddSecret.value = false;
    }
  } catch {}
}

async function deleteSecret(key: string) {
  try {
    const res = await fetch(`${API_BASE}/api/secrets/${key}`, {
      method: "DELETE",
    });
    if (res.ok) {
      secrets.value = secrets.value.filter((s) => s.key !== key);
    }
  } catch {}
}

async function importSecretsFromEnv() {
  try {
    await fetch(`${API_BASE}/api/secrets/import-env`, { method: "POST" });
    await fetchSecrets();
  } catch {}
}

// ── Global Settings ──────────────────────────────────────────────
const themeSettings = reactive({
  theme: "dark",
  fontSize: 16,
  palette: "default",
});

async function saveGlobalSettings() {
  try {
    await fetch(`${API_BASE}/api/system/settings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scope: "global", values: { ...themeSettings } }),
    });
  } catch {}
}

// ── User Settings ────────────────────────────────────────────────
const userSettings = reactive({
  displayName: "uDos Developer",
  email: "",
  defaultModel: "Llama 3.2",
});

async function saveUserSettings() {
  try {
    await fetch(`${API_BASE}/api/system/settings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scope: "user", values: { ...userSettings } }),
    });
  } catch {}
}

// ── Data Fetching ────────────────────────────────────────────────
async function fetchPages() {
  try {
    const res = await fetch(`${API_BASE}/api/system/pages`, {
      signal: AbortSignal.timeout(3000),
    });
    if (res.ok) {
      const data = await res.json();
      const pages = data.pages || [];
      allPages.value = pages.map((p: any) => ({
        id: p.id,
        title: p.title,
        icon: p.icon || "dashboard",
      }));
      if (allPages.value.length > 0) return;
    }
  } catch {}
  allPages.value = LOCAL_FALLBACK_PAGES;
}

async function fetchReadiness() {
  readinessLoading.value = true;
  readinessError.value = "";
  try {
    readinessSnapshot.value = await getCapabilitiesReadiness([
      "workflow.run",
      "knowledge.search",
      "ucode.grid",
      "developer.autonomous",
      "llm.openrouter",
      "identity_gateway",
      "wordpress_gateway",
    ]);
  } catch (e: any) {
    readinessError.value =
      e?.message || "Failed to load capability readiness snapshot";
  } finally {
    readinessLoading.value = false;
  }
}

async function fetchVariables() {
  loadingVars.value = true;
  try {
    const res = await fetch(`${API_BASE}/api/variables`, {
      signal: AbortSignal.timeout(3000),
    });
    if (res.ok) {
      const data = await res.json();
      userVariables.value = data.user || {};
      installVariables.value = data.installation || {};
    }
  } catch {}
  loadingVars.value = false;
}

async function fetchModelsConfig() {
  try {
    const res = await fetch(`${API_BASE}/api/models`, {
      signal: AbortSignal.timeout(3000),
    });
    if (res.ok) {
      const data = await res.json();
      modelsProviders.value = (data.providers || []).map((p: any) => ({
        id: p.id || "",
        name: p.name || p.id || "",
        models: Array.isArray(p.models) ? p.models : [],
      }));
    }
  } catch {}
}

async function fetchAgentsConfig() {
  try {
    const res = await fetch(`${API_BASE}/api/agents`, {
      signal: AbortSignal.timeout(3000),
    });
    if (res.ok) {
      const data = await res.json();
      const agents = Array.isArray(data.agents) ? data.agents : [];
      // Demote agents to config — show only config-defined agents
      agentConfigs.value = agents
        .filter((a: any) => a.config || a.id === a.name)
        .map((a: any) => ({
          id: a.id || "",
          name: a.name || a.id || "",
          provider: a.provider || "ollama",
          model: a.model || "",
          capabilities: Array.isArray(a.capabilities) ? a.capabilities : [],
        }));
    }
  } catch {}
}

async function fetchSecrets() {
  loadingSecrets.value = true;
  try {
    const res = await fetch(`${API_BASE}/api/secrets`, {
      signal: AbortSignal.timeout(3000),
    });
    if (res.ok) {
      const data = await res.json();
      const list = data.secrets || data || [];
      secrets.value = Array.isArray(list)
        ? list.map((s: any) => ({
            key: s.key || s.name,
            scope: s.scope || "user",
            value: s.masked || "••••••••",
          }))
        : [];
    }
  } catch {}
  loadingSecrets.value = false;
}

async function loadSettings() {
  try {
    const res = await fetch(`${API_BASE}/api/system/settings`, {
      signal: AbortSignal.timeout(3000),
    });
    if (res.ok) {
      const data = await res.json();
      const settings = data.settings || {};
      if (settings.global) {
        themeSettings.theme = settings.global.theme || "dark";
        themeSettings.fontSize = settings.global.fontSize || 16;
        themeSettings.palette = settings.global.palette || "default";
      }
      if (settings.user) {
        userSettings.displayName =
          settings.user.displayName || "uDos Developer";
        userSettings.email = settings.user.email || "";
        userSettings.defaultModel = settings.user.defaultModel || "Llama 3.2";
      }
    }
  } catch {}
}

onMounted(() => {
  if (!VALID_SYSTEM_TABS.has(routeTab) && routeTab) {
    router.replace({
      path: "/system",
      query: { ...route.query, tab: "pages" },
    });
  }
  fetchPages();
  fetchReadiness();
  fetchVariables();
  fetchModelsConfig();
  fetchAgentsConfig();
  fetchSecrets();
  loadSettings();
});

// Persist to localStorage as cache
watch(
  themeSettings,
  (v) => {
    try {
      localStorage.setItem("ucore-theme-settings", JSON.stringify(v));
    } catch {}
  },
  { deep: true },
);
watch(
  userSettings,
  (v) => {
    try {
      localStorage.setItem("ucore-user-settings", JSON.stringify(v));
    } catch {}
  },
  { deep: true },
);
</script>

<style scoped>
.surface__content {
  padding: var(--usx-spacing-lg);
}
.surface__panel-title {
  margin: 0 0 var(--usx-spacing-sm);
  font-size: var(--usx-font-size-lg);
  font-weight: var(--usx-font-weight-semibold);
}
.system-muted-copy {
  margin: 0 0 var(--usx-spacing-md);
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
}
.system-section-title {
  margin: var(--usx-spacing-md) 0 var(--usx-spacing-xs);
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-semibold);
}
.system-loading {
  padding: var(--usx-spacing-lg);
  text-align: center;
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
}
.system-panel {
  width: 100%;
  box-sizing: border-box;
}
.system-tab-shell {
  min-width: 0;
}

/* Pages */
.system-pages-grid {
  --system-grid-column-min: calc(var(--usx-touch-min) * 4.5);
  display: grid;
  grid-template-columns: repeat(
    auto-fit,
    minmax(min(100%, var(--system-grid-column-min)), 1fr)
  );
  gap: var(--usx-spacing-sm);
  min-width: 0;
}
.system-page-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-md);
  background: var(--usx-color-surface);
  border-radius: var(--usx-radius-lg);
  cursor: pointer;
  transition:
    background var(--usx-transition-fast),
    border-color var(--usx-transition-fast),
    transform var(--usx-transition-fast);
  border: 1px solid transparent;
}
.system-page-card:hover {
  border-color: var(--usx-color-primary);
}
.system-page-id {
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-primary);
}
.system-page-title {
  font-size: var(--usx-font-size-sm);
  text-align: center;
  overflow-wrap: anywhere;
}

.system-runtime-redirect {
  margin-top: var(--usx-spacing-lg);
}
.system-runtime-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--usx-spacing-sm);
}

.system-readiness {
  margin-bottom: var(--usx-spacing-lg);
}

.system-readiness-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--usx-spacing-sm);
}

.system-readiness-summary {
  display: flex;
  gap: var(--usx-spacing-md);
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
  margin-bottom: var(--usx-spacing-sm);
}

.system-readiness-list {
  margin: 0 0 var(--usx-spacing-sm);
  padding-left: var(--usx-spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
}

.system-readiness-item {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
}

.system-readiness-cap {
  font-family: var(--usx-font-family-mono);
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface);
}

.system-readiness-action {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
}

/* Variables */
.system-table-wrap {
  overflow-x: auto;
  margin-bottom: var(--usx-spacing-md);
}
.system-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--usx-font-size-sm);
}
.system-table th {
  text-align: left;
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface-muted);
  padding: var(--usx-spacing-sm);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
  white-space: nowrap;
}
.system-table td {
  padding: var(--usx-spacing-sm);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
  vertical-align: middle;
}
.system-var-key {
  font-family: var(--usx-font-family-mono);
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-primary);
  min-width: 14ch;
}
.system-var-value {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
  flex: 1;
}
.system-var-input {
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  background: var(--usx-color-background);
  border: 1px solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-sm);
  flex: 1;
}

/* Secrets */
.system-secrets-actions {
  display: flex;
  gap: var(--usx-spacing-sm);
  margin-bottom: var(--usx-spacing-md);
}
.system-action-btn {
  padding: var(--usx-spacing-xs) var(--usx-spacing-md);
  background: var(--usx-color-surface);
  border: 1px solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  color: var(--usx-color-on-surface);
  cursor: pointer;
  font-size: var(--usx-font-size-sm);
}
.system-action-btn:hover {
  background: var(--usx-color-background);
}
.system-save-settings-btn {
  margin-top: var(--usx-spacing-md);
}
.system-add-secret-form {
  display: flex;
  gap: var(--usx-spacing-sm);
  margin-bottom: var(--usx-spacing-md);
  padding: var(--usx-spacing-sm);
  background: var(--usx-color-background);
  border-radius: var(--usx-radius-md);
}
.system-secret-key {
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-medium);
  min-width: 14ch;
}
.system-secret-value {
  font-family: var(--usx-font-family-mono);
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
  flex: 1;
}
.system-secret-actions {
  display: inline-flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
}

/* Buttons */
.system-edit-btn,
.system-save-btn,
.system-delete-btn {
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  background: transparent;
  border: 1px solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  cursor: pointer;
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
}
.system-edit-btn:hover,
.system-save-btn:hover {
  color: var(--usx-color-primary);
  border-color: var(--usx-color-primary);
}
.system-delete-btn:hover {
  color: var(--usx-color-danger);
  border-color: var(--usx-color-danger);
}

/* Settings */
.system-settings-form {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
  margin-bottom: var(--usx-spacing-sm);
}
.settings-row {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-md);
  padding: var(--usx-spacing-sm) 0;
}
.settings-row label {
  min-width: 12ch;
  font-size: var(--usx-font-size-sm);
}
.settings-row select,
.settings-row input[type="text"],
.settings-row input[type="email"] {
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  background: var(--usx-color-background);
  border-radius: var(--usx-radius-sm);
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-sm);
  border: 1px solid var(--usx-color-border);
}
</style>

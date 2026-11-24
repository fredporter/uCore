<template>
  <div
    class="surface"
    :class="{
      'surface--tab-nav-vertical': shell.tabOrientation === 'vertical',
    }"
  >
    <SurfaceTabNav
      v-model="activeTab"
      :tabs="visibleSystemTabs"
      :orientation="shell.tabOrientation"
      @toggle-orientation="shell.toggleTabOrientation()"
    />
    <div class="surface__content">
      <section v-if="currentTab === 'preferences'" class="system-panel system-tab-shell">
        <div class="settings-heading"><h2>Settings</h2><button class="usx-btn" @click="router.push('/setup')">User Setup Story</button></div>
        <div class="system-settings-form">
          <label class="settings-row"><span>Show Advanced</span><input type="checkbox" :checked="preferences.advancedView" @change="preferences.setAdvancedView(($event.target as HTMLInputElement).checked)" /></label>
          <p class="system-muted-copy">Show engineering, diagnostics, configuration and administration tools.</p>
          <label class="settings-row"><span>Appearance</span><select :value="preferences.themeMode" @change="preferences.setThemeMode(($event.target as HTMLSelectElement).value as 'light' | 'dark' | 'auto')"><option value="dark">Dark</option><option value="light">Light</option><option value="auto">Automatic</option></select></label>
          <label class="settings-row"><span>Reading font</span><select :value="preferences.readingFont" @change="preferences.setReadingFont(($event.target as HTMLSelectElement).value as ReadingFont)"><option value="serif">Serif</option><option value="sans">Sans</option><option value="mono">Mono</option></select></label>
          <label class="settings-row">
            <span>Terminology pack</span>
            <select v-model="preferences.terminologyPack">
              <option v-for="(label, pack) in terminologyPacks" :key="pack" :value="pack">{{ label }}</option>
            </select>
          </label>
          <label class="settings-row"><span>Text size</span><input type="number" min="12" max="24" :value="preferences.fontSize" @change="preferences.setFontSize(Number(($event.target as HTMLInputElement).value))" /></label>
        </div>
        <p v-if="preferences.syncError" role="status">{{ preferences.syncError }} · Settings are kept on this device.</p>
      </section>
      <AppsManagerPanel v-if="currentTab === 'apps'" />
      <GitHubCIPanel v-if="currentTab === 'github'" />
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
            <UBadge v-else-if="readinessError" type="warning" size="sm"
              >unavailable</UBadge
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

          <div class="system-readiness-summary">
            <span>Ollama: {{ checkingOllama ? "checking" : ollama?.online ? `online · ${ollama.models.length} installed models` : "unavailable" }}</span>
            <span>OpenRouter (optional): {{ openRouterReadiness?.ready ? "configured" : openRouterReadiness ? "setup needed" : "not checked" }}</span>
          </div>
          <p class="system-muted-copy">Provider checks report host availability and configuration. They do not verify uCode+ inference.</p>
          <form v-if="openRouterReadiness && !openRouterReadiness.ready" class="readiness-repair" @submit.prevent="saveOpenRouterModel">
            <label for="openrouter-model">OpenRouter model</label>
            <input id="openrouter-model" v-model="openRouterModel" placeholder="provider/model" required />
            <button class="usx-btn" type="submit" :disabled="repairingOpenRouter">Save and re-check</button>
            <p v-if="openRouterRepairError" role="alert">{{ openRouterRepairError }}</p>
          </form>
          <button class="usx-btn system-action-btn" @click="refreshReadiness">
            Re-check readiness
          </button>
        </div>

        <div class="system-pages-grid">
          <button
            v-for="page in allPages"
            :key="page.id"
            class="system-page-card"
            type="button"
            @click="navigateToPage(page.id)"
          >
            <UIcon :name="page.icon" />
            <span class="system-page-id">{{ page.id }}</span>
            <span class="system-page-title">{{ page.title }}</span>
          </button>
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
              class="usx-btn system-action-btn"
              @click="goTo('/snackbar?tab=dashboard')"
            >
              Open Server Overview
            </button>
            <button
              class="usx-btn system-action-btn"
              @click="goTo('/snackbar?tab=services')"
            >
              Open Server Services
            </button>
            <button
              class="usx-btn system-action-btn"
              @click="goTo('/snackbar?tab=automation')"
            >
              Open Server Automation
            </button>
          </div>
        </div>
      </div>

      <section v-if="currentTab === 'configuration'" class="system-panel system-tab-shell">
        <h3 class="surface__panel-title">Device</h3>
        <p v-if="installVariablesError" class="system-muted-copy" role="status">{{ installVariablesError }}</p>
        <button v-if="installVariablesError" type="button" class="usx-btn" :disabled="loadingInstallVariables" @click="fetchVariables">
          <UIcon name="refresh" /> Retry device details
        </button>
        <div class="system-settings-form">
          <div v-if="installVariables.hostname" class="settings-row"><span>Hostname</span><output>{{ installVariables.hostname }}</output></div>
          <div v-if="installVariables.platform" class="settings-row"><span>Platform</span><output>{{ installVariables.platform }}</output></div>
          <div class="settings-row"><span>Timezone</span><output>{{ deviceTimezone }}</output></div>
          <div class="settings-row"><span>Appearance</span><output>{{ preferences.themeMode === 'auto' ? 'Automatic' : preferences.themeMode }}</output></div>
          <div class="settings-row"><span>Text size</span><output>{{ preferences.fontSize }} px</output></div>
        </div>
        <button type="button" class="usx-btn" @click="activeTab = 'identity'"><UIcon name="person" />Profiles</button>

        <h3 class="surface__panel-title">Ollama</h3>
        <p class="system-muted-copy" role="status">{{ checkingOllama ? 'Checking Ollama…' : ollama?.online ? 'Running locally' : 'Ollama is unavailable' }}</p>
        <ul v-if="ollama?.models.length">
          <li v-for="model in ollama.models" :key="model.name">{{ model.name }}</li>
        </ul>
        <p v-else-if="ollama?.online" class="system-muted-copy">No local models installed.</p>
        <button type="button" class="usx-btn" :disabled="checkingOllama" @click="fetchOllamaStatus"><UIcon name="refresh" />Check Ollama</button>
      </section>

      <!-- Secrets -->
      <div
        v-if="currentTab === 'configuration'"
        class="system-panel system-tab-shell"
      >
        <OAuthSettingsPanel />
        <h3 class="surface__panel-title">Secret Store</h3>
        <p class="system-muted-copy">
          Encrypted secret storage. Values are masked by default.
        </p>
        <h4 class="system-section-title">GitHub integration token</h4>
        <p class="system-muted-copy">{{ loadingSecrets ? 'Loading credentials…' : secrets.some(secret => secret.key === 'GITHUB_TOKEN') ? 'GitHub token stored. Connection status is unverified.' : 'Add a token for uCore integrations.' }}</p>
        <p class="system-muted-copy">Git pushes use the credentials configured in your development environment.</p>
        <p v-if="secretSaveError" class="system-muted-copy" role="alert">{{ secretSaveError }}</p>
        <p v-if="secretSaved" class="system-muted-copy" role="status">{{ secretSaved }}</p>
        <button type="button" class="usx-btn" @click="newSecretKey = 'GITHUB_TOKEN'; newSecretValue = ''; showAddSecret = true"><UIcon name="key" />Set GitHub token</button>
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
          <button class="system-save-btn" :disabled="savingSecret || !newSecretKey.trim() || !newSecretValue.trim()" @click="addSecret">{{ savingSecret ? 'Saving…' : 'Save' }}</button>
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

      <!-- User Settings & Identity -->
      <div
        v-if="currentTab === 'identity'"
        class="system-panel system-tab-shell"
      >
        <h3 class="surface__panel-title">Profiles</h3>
        <p class="system-muted-copy">
          Your username, publishing role and Setup Story details.
        </p>
        <div class="system-settings-form">
          <div class="settings-row"><label for="profile-name">Username</label><input id="profile-name" type="text" v-model="userSettings.displayName" /></div>
          <div class="settings-row">
            <label for="profile-role">Role</label>
            <select id="profile-role" v-model="userSettings.publishingRole" :disabled="!identityStore.authenticated">
              <option v-for="role in ROLE_OPTIONS" :key="role" :value="role.toLowerCase()">{{ role }}</option>
            </select>
          </div>
          <div class="settings-row"><label>Location</label><output>{{ profileLocation || 'Set in Setup Story' }}</output></div>
          <div class="settings-row"><label>Device timezone</label><output>{{ deviceTimezone }}</output></div>
          <div v-if="identityStore.identity?.user_id" class="settings-row"><label>User UID</label><output class="profile-id">{{ identityStore.identity.user_id }}</output></div>
          <div v-if="identityStore.identity?.install_id" class="settings-row"><label>Installation UID</label><output class="profile-id">{{ identityStore.identity.install_id }}</output></div>
          <div v-if="identityStore.profiles.length>1" class="settings-row"><label for="profile-switch">Switch profile</label><select id="profile-switch" :value="identityStore.activeProfileId" @change="identityStore.switchProfile(($event.target as HTMLSelectElement).value)"><option v-for="profile in identityStore.profiles" :key="profile.id" :value="profile.id">{{ profile.name }}</option></select></div>
          <div class="settings-row">
            <label>Authentication</label>
            <div class="profile-auth-row">
              <span class="profile-auth-status" :class="identityStore.authenticated ? 'profile-auth-status--signed-in' : 'profile-auth-status--signed-out'">
                {{ identityStore.authenticated ? 'Signed in' : 'Signed out' }}
              </span>
              <button
                v-if="identityStore.authenticated"
                type="button"
                class="usx-btn usx-btn--secondary"
                @click="identityStore.logout()"
              >
                Log Out
              </button>
              <button
                v-else
                type="button"
                class="usx-btn usx-btn--primary"
                @click="identityStore.login('default')"
              >
                Log In
              </button>
            </div>
          </div>
          <div class="settings-row">
            <label for="profile-email">Email</label>
            <input
              id="profile-email"
              type="email"
              v-model="userSettings.email"
              placeholder="user@example.com"
            />
          </div>
        </div>
        <p v-if="profileError" role="alert" class="profile-error">{{ profileError }}</p>
        <p v-if="profileSaved" role="status">Profile saved.</p>
        <button
          class="usx-btn system-save-settings-btn"
          :disabled="savingProfile || !identityStore.authenticated"
          @click="saveUserSettings(false)"
        >{{ savingProfile ? "Saving…" : "Save Profile" }}</button>
        <button
          class="usx-btn system-save-settings-btn"
          :disabled="savingProfile || !identityStore.authenticated"
          @click="saveUserSettings(true)"
        >
          <UIcon name="arrow_forward" />{{ savingProfile ? "Saving…" : "Save and Open Setup Story" }}
        </button>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import type { TabDef } from "../../skills/molecules/SurfaceTabNav.vue";

export const SYSTEM_TABS: TabDef[] = [
  { id: "preferences", label: "Settings", icon: "tune" },
  { id: "apps", label: "Apps", icon: "apps" },
  { id: "pages", label: "Pages", icon: "dashboard" },
  { id: "github", label: "GitHub", icon: "code" },
  { id: "configuration", label: "Configuration", icon: "tune" },
  { id: "identity", label: "Profiles", icon: "person" },
];
</script>

<script setup lang="ts">
import { computed, ref, reactive, watch, onMounted } from "vue";
import OAuthSettingsPanel from "./OAuthSettingsPanel.vue";
import GitHubCIPanel from "./GitHubCIPanel.vue";
import { useRouter, useRoute } from "vue-router";
import { terminologyPacks, useSettingsStore, type ReadingFont } from "../../stores/settings";
import { useShellStore } from "../../stores/shell";
import { useIdentityStore, ROLE_OPTIONS } from "../../stores/identity";
import { SNACKBAR_BASE, UCORE_BASE } from "../../api/base";
import {
  getCapabilitiesReadiness,
  type CapabilityReadinessSnapshot,
  type CapabilityPreflightResult,
} from "../../api/preflight";
import AppsManagerPanel from "./AppsManagerPanel.vue";
import UIcon from "../../skills/atoms/UIcon.vue";
import UBadge from "../../skills/atoms/UBadge.vue";
import SurfaceTabNav from "../../skills/molecules/SurfaceTabNav.vue";

const API_BASE = SNACKBAR_BASE;
const route = useRoute();
const router = useRouter();
const shell = useShellStore();
const identityStore = useIdentityStore();
const preferences = useSettingsStore();
const visibleSystemTabs = computed(() => SYSTEM_TABS.filter(tab => preferences.advancedView || ['preferences', 'apps', 'identity'].includes(tab.id)));
const VALID_SYSTEM_TABS = new Set(SYSTEM_TABS.map((tab) => tab.id));

const routeTab = String(route.query.tab || "");
const LEGACY_SYSTEM_TABS: Record<string, string> = {
  connections: "apps",
  variables: "configuration",
  secrets: "configuration",
  "global-settings": "configuration",
  "user-settings": "identity",
};
const initialTab = LEGACY_SYSTEM_TABS[routeTab] || routeTab;
const activeTab = ref(visibleSystemTabs.value.some(tab => tab.id === initialTab) ? initialTab : "preferences");
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
    (cap) => !cap.ready && cap.capability !== "llm.openrouter",
  );
});

const openRouterReadiness = computed(() => readinessSnapshot.value?.capabilities.find(cap => cap.capability === "llm.openrouter"));

const readinessBlockedCount = computed(() => blockedCapabilities.value.length);

function navigateToPage(pageId: string) {
  router.push(`/system/${pageId.toLowerCase()}`);
}

function goTo(path: string) {
  router.push(path);
}

// ── Variables ────────────────────────────────────────────────────
const installVariables = ref<Record<string, string>>({});
const installVariablesError = ref("");
const loadingInstallVariables = ref(false);
const ollama = ref<{ online: boolean; models: { name: string }[] } | null>(null);
const checkingOllama = ref(false);

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
const savingSecret = ref(false);
const secretSaveError = ref("");
const secretSaved = ref("");

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
  if (!key || !value || savingSecret.value) return;
  savingSecret.value = true;
  secretSaveError.value = "";
  secretSaved.value = "";
  try {
    const res = await fetch(`${API_BASE}/api/secrets/${encodeURIComponent(key)}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ value }),
    });
    if (!res.ok) {
      secretSaveError.value = `The secret could not be saved (HTTP ${res.status}). Check the local service and try again.`;
      return;
    }
    const existing = secrets.value.findIndex(secret => secret.key === key);
    const updated = { key, scope: secrets.value[existing]?.scope ?? "user", value: "••••••••" };
    if (existing < 0) secrets.value.push(updated);
    else secrets.value[existing] = updated;
    newSecretKey.value = "";
    newSecretValue.value = "";
    showAddSecret.value = false;
    secretSaved.value = `${key} saved to the uCore Secret Store.`;
  } catch {
    secretSaveError.value = "The local secret service is unavailable. Check the connection and retry.";
  } finally {
    savingSecret.value = false;
  }
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

// ── User Settings ────────────────────────────────────────────────
const userSettings = reactive({
  displayName: "",
  email: "",
  publishingRole: "wizard",
});

const savingProfile = ref(false);
const profileError = ref("");
const profileSaved = ref(false);
const profileLocation = ref("");
const deviceTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
const profileRole = computed(() => {
  const role = identityStore.activeProfile?.role.toLowerCase();
  if (!identityStore.authenticated || !role) return "—";
  if (role === "wizard" || role === "owner") return "Wizard";
  if (role === "sorcerer" || role === "sorceror") return "Sorceror";
  if (["knight", "user", "guest", "developer"].includes(role)) return "Knight";
  if (["crypt", "drone", "tomb", "ghost"].includes(role)) return role.charAt(0).toUpperCase() + role.slice(1);
  return role;
});

// Canonical lowercase option values shown by the Role selector.
const ROLE_VALUES = ROLE_OPTIONS.map((role) => role.toLowerCase());
function normalizeRole(value: string): string {
  const role = String(value || "").toLowerCase();
  if (role === "sorcerer") return "sorceror";
  if (role === "owner") return "wizard";
  if (["user", "guest", "developer"].includes(role)) return "knight";
  return ROLE_VALUES.includes(role) ? role : "wizard";
}

watch([currentTab, () => identityStore.activeProfileId], async ([tab, profile], _old, onCleanup) => {
  profileLocation.value = "";
  userSettings.displayName = "";
  userSettings.email = "";
  userSettings.publishingRole = normalizeRole(profileRole.value);
  if (tab !== "identity" || !profile) return;
  const request = new AbortController();
  onCleanup(() => request.abort());
  try {
    const response = await fetch(`${UCORE_BASE}/api/connections`, { signal: request.signal });
    if (!response.ok || request.signal.aborted) return;
    const state = await response.json();
    if (request.signal.aborted) return;
    const story = state.setup_story?.responses || {};
    const variables = state.user_profile || {};
    if (!userSettings.displayName) {
      userSettings.displayName = String(state.setup?.display_name || variables.display_name || identityStore.activeProfile?.name || "").trim()
        || `user-${profile.split("-").at(-1)?.toLowerCase()}`;
    }
    if (!userSettings.email) userSettings.email = String(variables.email ?? story.email ?? state.setup?.answers?.email ?? "");
    if (variables.publishing_role) userSettings.publishingRole = normalizeRole(String(variables.publishing_role));
    profileLocation.value = [story.city ?? variables.city, story.country ?? variables.country].filter(Boolean).join(", ");
  } catch {}
}, { immediate: true });

async function saveUserSettings(openSetup: boolean) {
  if (savingProfile.value || !identityStore.authenticated) return;
  const profile = identityStore.activeProfileId;
  savingProfile.value = true;
  profileError.value = "";
  profileSaved.value = false;
  try {
    const response = await fetch(`${UCORE_BASE}/api/connections/setup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        save_profile: true,
        display_name: userSettings.displayName,
        answers: { email: userSettings.email, publishing_role: userSettings.publishingRole },
      }),
    });
    if (!response.ok) throw Error(await response.text() || "Profile could not be saved");
    if (identityStore.activeProfileId !== profile) return;
    const saved = await response.json();
    userSettings.displayName = saved.display_name || userSettings.displayName;
    await identityStore.load();
    if (identityStore.activeProfileId !== profile) return;
    profileSaved.value = true;
    if (openSetup) await router.push("/setup");
  } catch (error) {
    profileError.value = error instanceof Error ? error.message : "Profile could not be saved";
  } finally {
    savingProfile.value = false;
  }
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

const openRouterModel = ref("");
const repairingOpenRouter = ref(false);
const openRouterRepairError = ref("");

async function saveOpenRouterModel() {
  const model = openRouterModel.value.trim();
  if (!model || repairingOpenRouter.value) return;
  repairingOpenRouter.value = true;
  openRouterRepairError.value = "";
  try {
    const response = await fetch(`${UCORE_BASE}/api/variables/user`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ openrouter_model: model }),
    });
    if (!response.ok || (await response.json()).variables?.openrouter_model !== model) {
      throw new Error("Could not save the OpenRouter model.");
    }
    await fetchReadiness();
  } catch (error) {
    openRouterRepairError.value = error instanceof Error ? error.message : "Could not save the OpenRouter model.";
  } finally {
    repairingOpenRouter.value = false;
  }
}

function refreshReadiness() {
  void fetchReadiness();
  void fetchOllamaStatus();
}

async function fetchReadiness() {
  readinessLoading.value = true;
  readinessError.value = "";
  try {
    readinessSnapshot.value = await getCapabilitiesReadiness([
      "workflow.run",
      "knowledge.search",
      "ucode.grid",
      "developer.guided",
      "llm.openrouter",
      "identity_gateway",
      "wordpress_gateway",
    ]);
  } catch (e: any) {
    readinessSnapshot.value = null;
    const message = String(e?.message || "");
    readinessError.value = /json|http|unexpected/i.test(message)
      ? "Readiness service is unavailable. Local recovery pages remain available."
      : message || "Failed to load capability readiness snapshot";
  } finally {
    readinessLoading.value = false;
  }
}

async function fetchVariables() {
  if (loadingInstallVariables.value) return;
  loadingInstallVariables.value = true;
  try {
    const res = await fetch(`${API_BASE}/api/variables/install`, {
      signal: AbortSignal.timeout(3000),
    });
    if (!res.ok) throw new Error("Device details unavailable");
    const data = await res.json();
    if (!data || typeof data !== "object" || Array.isArray(data)) throw new Error("Invalid device details");
    installVariables.value = data;
    installVariablesError.value = "";
  } catch {
    installVariablesError.value = "Device details are unavailable. Timezone and appearance still use your current device settings.";
  } finally {
    loadingInstallVariables.value = false;
  }
}

async function fetchOllamaStatus() {
  checkingOllama.value = true;
  try {
    const response = await fetch(`${UCORE_BASE}/api/ollama/status`, { signal: AbortSignal.timeout(6000) });
    if (!response.ok) throw new Error("Could not check Ollama");
    const status = await response.json();
    ollama.value = { online: !!status.online, models: Array.isArray(status.models) ? status.models : [] };
  } catch {
    ollama.value = null;
  } finally {
    checkingOllama.value = false;
  }
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
    const profileId = identityStore.activeProfileId || "default";
    const res = await fetch(`${API_BASE}/api/system/settings?profile=${encodeURIComponent(profileId)}`, {
      headers: { "X-Udos-Profile": profileId },
      signal: AbortSignal.timeout(3000),
    });
    if (res.ok) {
      const data = await res.json();
      const settings = data.settings || {};
      if (settings.user) {
        userSettings.displayName =
          identityStore.displayName || settings.user.displayName || "Local user";
        userSettings.email = settings.user.email || "";
      }
    }
  } catch {}
}

function loadAdvancedSettings() {
  void fetchPages(); void fetchReadiness();
}
watch(currentTab, tab => {
  if (tab !== "configuration") return;
  void fetchVariables();
  void fetchOllamaStatus();
  void fetchSecrets();
}, { immediate: true });

watch(() => preferences.advancedView, enabled => {
  if (enabled) loadAdvancedSettings();
  if (!visibleSystemTabs.value.some(tab => tab.id === activeTab.value)) activeTab.value = "preferences";
});
onMounted(async () => {
  if (String(route.query.tab || "") !== activeTab.value) {
    router.replace({ path: "/system", query: { ...route.query, tab: activeTab.value } });
  }
  await identityStore.load();
  if (preferences.advancedView) loadAdvancedSettings();
  loadSettings();
});

watch(() => identityStore.activeProfileId, () => {
  loadSettings();
});

watch(activeTab, (tab) => {
  if (String(route.query.tab || "") === tab) return;
  router.replace({ path: "/system", query: { ...route.query, tab } });
});

// Persist to localStorage as cache
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
  padding: clamp(var(--usx-spacing-md), 4vw, calc(var(--usx-spacing-xl) * 2));
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
  max-width: 64rem;
  margin-inline: auto;
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
  color: inherit;
  font: inherit;
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

/* One control edge and a shared label column for ordinary preferences. */
.system-settings-form > .settings-row { display:grid; grid-template-columns:10rem minmax(0,24rem); align-items:center; gap:12px; min-height:32px; margin:0; padding:4px 0; font-size:var(--usx-font-size-sm); }
.system-settings-form > .settings-row > span { white-space:nowrap; }
.system-settings-form > .settings-row > :is(select,input:not([type=checkbox])) { box-sizing:border-box; width:100%; height:32px; min-height:32px; margin:0; padding:4px 8px; border:1px solid var(--usx-color-border); border-radius:var(--usx-radius-sm); background:var(--usx-color-surface); color:var(--usx-color-on-surface); box-shadow:none; outline:0; font:inherit; line-height:1.2; }
.system-settings-form > .settings-row > :is(select,input:not([type=checkbox])):focus-visible { border-color:transparent; outline:2px solid var(--usx-color-primary); outline-offset:-2px; box-shadow:none; }
.system-settings-form > .settings-row > input[type=checkbox] { justify-self:start; width:18px; height:18px; min-height:0; margin:0; accent-color:var(--usx-color-primary); box-shadow:none; }
.system-settings-form > .system-muted-copy { margin:0 0 8px; font-size:var(--usx-font-size-sm); }
@media(max-width:30rem){.system-settings-form > .settings-row {grid-template-columns:8rem minmax(0,1fr);gap:8px;}}

.settings-heading{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;}.settings-heading .usx-btn{min-height:32px;margin:0;padding:4px 8px;font-size:var(--usx-font-size-sm);}
.profile-id{overflow-wrap:anywhere;}
.profile-auth-row{display:flex;align-items:center;justify-content:space-between;gap:12px;min-height:32px;font-size:var(--usx-font-size-sm);}
.profile-auth-row .usx-btn{min-height:32px;margin:0;padding:4px 12px;font-size:var(--usx-font-size-sm);}
.profile-auth-status{font-weight:var(--usx-font-weight-semibold);font-size:inherit;}
.profile-auth-status--signed-in{color:var(--usx-color-success);}
.profile-auth-status--signed-out{color:var(--usx-color-danger);}
.profile-error{color:var(--usx-color-danger);font-size:var(--usx-font-size-sm);margin:var(--usx-spacing-xs) 0 0;}
.system-settings-form>.settings-row>label{margin:0;min-width:0;}
.system-settings-form>.settings-row>output{font-size:var(--usx-font-size-sm);color:var(--usx-color-on-surface);line-height:1.4;}
.system-settings-form > .settings-row > label { align-self: center; line-height: 1.25; padding: 0; }
.readiness-repair { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }
.readiness-repair input { flex: 1 1 12rem; min-width: 0; }
</style>

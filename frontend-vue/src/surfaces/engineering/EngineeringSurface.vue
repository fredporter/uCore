<template>
  <div class="engineering-surface" :class="{ 'engineering-surface--vertical': shell.tabOrientation === 'vertical' }">
    <SurfaceTabNav
      v-model="engineeringTab"
      :tabs="tabs"
      :orientation="shell.tabOrientation"
      aria-label="Engineering"
      @toggle-orientation="shell.toggleTabOrientation()"
    />
    <div class="engineering-content" :class="{ 'engineering-content--tools': engineeringTab === 'tools' }">
      <RecipeGallerySurface
        v-if="engineeringTab !== 'tools'"
        :lane="engineeringTab === 'grid-recipes' ? 'gridcore' : 'usx'"
      />
      <template v-else>
          <nav class="engineering-actions" aria-label="Developer tools shortcuts">
            <a class="usx-btn" href="http://127.0.0.1:3484/ucore" target="_blank" rel="noopener noreferrer"><UIcon name="launch" /> Open Cline Kanban</a>
            <a class="usx-btn" href="http://127.0.0.1:3484/ucode" target="_blank" rel="noopener noreferrer"><UIcon name="view_kanban" /> uCode Dev Roadmap</a>
          </nav>
          <header class="doc-engineering-heading">
            <h1>Developer tools</h1>
            <p>Develop uDOS in VS Code. Open the shared workspace from macOS Terminal.</p>
          </header>

          <div class="doc-health-strip">
            <div class="doc-health-item">
              <span class="doc-health-label">Sites API</span>
              <UBadge size="sm" :type="statusType(apiStatus.sites)">
                {{ statusText(apiStatus.sites) }}
              </UBadge>
            </div>
            <div class="doc-health-item">
              <span class="doc-health-label">Knowledge API</span>
              <UBadge size="sm" :type="statusType(apiStatus.knowledge)">
                {{ statusText(apiStatus.knowledge) }}
              </UBadge>
            </div>
            <div class="doc-health-item">
              <span class="doc-health-label">Courses API</span>
              <UBadge size="sm" :type="statusType(apiStatus.courses)">
                {{ statusText(apiStatus.courses) }}
              </UBadge>
            </div>
            <div class="doc-health-item">
              <span class="doc-health-label">Export API</span>
              <UBadge size="sm" :type="statusType(apiStatus.export)">
                {{ statusText(apiStatus.export) }}
              </UBadge>
            </div>
          </div>

          <!-- Developer & Engineering Tooling Content -->
          <section class="doc-developer-section" aria-label="Developer tools">
            <div class="doc-tool-grid">
              <div class="doc-tool-card">
                <div class="doc-tool-card-heading">
                  <UIcon name="computer" />
                  <h4>VS Code and GitHub Copilot</h4>
                </div>
                <p>Use Copilot inline suggestions and Chat for quick edits, small fixes, and focused explanations.</p>
                <div><code>code ~/Code/uDOS.code-workspace</code></div>
              </div>

              <div class="doc-tool-card">
                <div class="doc-tool-card-heading">
                  <UIcon name="code" />
                  <h4>Cline in VS Code and Cline CLI</h4>
                </div>
                <p>Use scoped development rounds in either client. Review the plan, keep approvals bounded, and verify with repository checks.</p>
                <div><code>cline --cwd ~/Code -p "plan this change"</code></div>
              </div>

              <div class="doc-tool-card">
                <div class="doc-tool-card-heading">
                  <UIcon name="terminal" />
                  <h4>Command launcher</h4>
                </div>
                <p>Select reviewed Engineering commands with ucdev, or active-profile personal workflows with ucusr. uFlow owns personal workflows and run receipts.</p>
                <div><code>uc · ucdev · ucusr</code></div>
              </div>

              <div class="doc-tool-card">
                <div class="doc-tool-card-heading">
                  <UIcon name="hub" />
                  <h4>Model Context Protocol (MCP)</h4>
                </div>
                <p>Connect approved tools through uCore service contracts and the active profile’s permissions.</p>
              </div>

              <div class="doc-tool-card">
                <div class="doc-tool-card-heading">
                  <UIcon name="screenshot" />
                  <h4>Visual review</h4>
                </div>
                <p>Review surfaces in Safari at desktop and narrow widths, and capture the same routes through Playwright WebKit for a repeatable record.</p>
                <div><code>ucdev · check-visual</code></div>
              </div>

              <div class="doc-tool-card">
                <div class="doc-tool-card-heading">
                  <UIcon name="article" />
                  <h4>Obsidian Baseline Authoring</h4>
                </div>
                <p>Obsidian is the primary user authoring standard for notes, binders, and canvases. Filesystem authority with zero database lock-in.</p>
                <div><code>~/Vault · ~/Shared · ~/Public</code></div>
              </div>
            </div>

            <div class="doc-section">
              <h4 class="doc-section-title">Workspace storage</h4>
              <ul class="doc-storage-list">
                  <li><strong>Repository Source:</strong> All repos belong under <code>~/Code/&lt;repo&gt;</code>.</li>
                  <li><strong>Mutable State:</strong> Owned by <code>UDOS_HOME</code> (default <code>~/Code/.udos</code>). Never write state directly to <code>$HOME</code>.</li>
                  <li><strong>User Documents:</strong> Pure UTF-8 markdown in <code>~/Vault</code>, <code>~/Shared</code>, and <code>~/Public</code>.</li>
                  <li><strong>Validation:</strong> Run <code>python3 scripts/check_home_path_policy.py</code> before committing path changes.</li>
              </ul>
            </div>
          </section>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, defineAsyncComponent, reactive, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useShellStore } from "../../stores/shell";
import UIcon from "../../skills/atoms/UIcon.vue";
import UBadge from "../../skills/atoms/UBadge.vue";
import SurfaceTabNav from "../../skills/molecules/SurfaceTabNav.vue";

const RecipeGallerySurface = defineAsyncComponent(async () => (await import("../recipes/RecipeGallerySurface.vue")).default);
const shell = useShellStore();
const route = useRoute();
const router = useRouter();
const tabs = [
  { id: "tools", label: "Tools", icon: "terminal" },
  { id: "recipes", label: "Prose Recipes", icon: "article" },
  { id: "grid-recipes", label: "Grid Recipes", icon: "grid_on" },
];
const engineeringTab = computed({
  get: () => {
    const section = route.query.section;
    return section === "recipes" || section === "grid-recipes" ? section : "tools";
  },
  set: (tab: string) => {
    void router.replace({ query: { ...route.query, section: tab === "tools" ? undefined : tab }, hash: route.hash });
  },
});

type ApiStatus = "pending" | "ok" | "error";
const apiStatus = reactive<Record<"sites" | "knowledge" | "courses" | "export", ApiStatus>>({
  sites: "pending",
  knowledge: "pending",
  courses: "pending",
  export: "pending",
});
const endpoints = {
  sites: "sites",
  knowledge: "global-knowledge",
  courses: "courses",
  export: "export",
} as const;

async function probe(key: keyof typeof endpoints) {
  apiStatus[key] = "pending";
  try {
    const response = await fetch(`/api/docs/${endpoints[key]}`, { signal: AbortSignal.timeout(5000) });
    apiStatus[key] = response.ok ? "ok" : "error";
  } catch {
    apiStatus[key] = "error";
  }
}

watch(engineeringTab, tab => {
  if (tab === "tools") void Promise.all((Object.keys(endpoints) as (keyof typeof endpoints)[]).map(probe));
}, { immediate: true });

function statusType(status: ApiStatus): "success" | "warning" | "error" {
  if (status === "ok") return "success";
  if (status === "error") return "error";
  return "warning";
}

function statusText(status: ApiStatus): string {
  if (status === "ok") return "Online";
  if (status === "error") return "Offline";
  return "Checking";
}

</script>

<style scoped>
.engineering-surface {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-width: 0;
  overflow: hidden;
}
.engineering-surface--vertical { flex-direction: row; }
.engineering-content {
  flex: 1;
  min-width: 0;
  min-height: 0;
  overflow: auto;
  padding: 0 var(--usx-spacing-md) var(--usx-spacing-md);
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
}

.engineering-content--tools {
  padding-block-start: var(--usx-spacing-sm);
  gap: var(--usx-spacing-md);
}

.engineering-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-start;
  gap: var(--usx-spacing-sm);
  margin: 0;
  padding: 0;
}

.engineering-actions .usx-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  min-height: var(--usx-touch-min-sm);
  margin: 0;
  padding: 0 var(--usx-spacing-sm);
  border: 0;
  background: transparent;
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
  text-decoration: none;
}

.engineering-actions .usx-btn:hover {
  color: var(--usx-color-primary);
}
.doc-developer-section,
.doc-engineering-heading {
  display: grid;
  gap: var(--usx-spacing-md);
  min-width: 0;
}

.doc-developer-section {
  margin: 0;
  padding: 0;
  gap: var(--usx-spacing-md);
}

.doc-engineering-heading {
  gap: var(--usx-spacing-xs);
  margin: 0;
}

.doc-engineering-heading h1 {
  font-size: var(--usx-font-size-xl);
}

.doc-tool-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 15rem), 1fr));
  gap: var(--usx-spacing-md);
}

.doc-engineering-heading,
.doc-tool-card,
.doc-storage-list {
  padding: var(--usx-spacing-md);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  background: var(--usx-color-surface);
}

.doc-tool-card {
  display: grid;
  grid-template-rows: auto 1fr auto;
  gap: var(--usx-spacing-sm);
  min-width: 0;
}

.doc-tool-card-heading {
  display: flex;
  align-items: flex-start;
  gap: var(--usx-spacing-sm);
}

.doc-tool-card-heading > :first-child {
  flex-shrink: 0;
}

.doc-engineering-heading > *,
.doc-tool-card h4,
.doc-tool-card p,
.doc-storage-list {
  margin: 0;
}

.doc-engineering-heading p,
.doc-tool-card p {
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
}

.doc-tool-card code {
  font-size: var(--usx-font-size-xs);
  overflow-wrap: anywhere;
}

.doc-storage-list {
  display: grid;
  gap: var(--usx-spacing-xs);
  padding-inline-start: var(--usx-spacing-xl);
  font-size: var(--usx-font-size-sm);
  overflow-wrap: anywhere;
}

.doc-health-strip {
  --doc-column-min: calc(var(--usx-touch-min) * 3);
  display: grid;
  grid-template-columns: repeat(
    auto-fit,
    minmax(min(100%, var(--doc-column-min)), 1fr)
  );
  gap: var(--usx-spacing-sm);
  min-width: 0;
}

.doc-health-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
}

.doc-health-label {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
}

.doc-section {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
}

.doc-section-title {
  margin: 0;
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface-muted);
  text-transform: uppercase;
  letter-spacing: var(--usx-letter-spacing-wide);
}

</style>

<template>
  <div class="surface">
    <div class="surface__content">
      <div class="developer-gateway">
        <header class="developer-gateway__header">
          <h1 class="developer-gateway__title">Developer Surface</h1>
          <p class="developer-gateway__subtitle">
            Launch and monitor the uDev developer server.
          </p>
        </header>

        <section
          class="developer-gateway__card"
          aria-label="developer-server-status"
        >
          <div class="developer-gateway__status-row">
            <span class="developer-gateway__status-label">Server Status</span>
            <strong
              class="developer-gateway__status-value"
              :class="{
                'developer-gateway__status-value--online': status.active,
                'developer-gateway__status-value--offline': !status.active,
              }"
            >
              {{ status.active ? "Running" : "Stopped" }}
            </strong>
          </div>

          <p class="developer-gateway__message">{{ status.message }}</p>

          <div class="developer-gateway__actions">
            <button
              class="developer-gateway__btn"
              :disabled="starting || refreshing"
              @click="refreshStatus"
            >
              {{ refreshing ? "Checking..." : "Refresh" }}
            </button>
            <button
              v-if="hasUdevRepo && !status.active"
              class="developer-gateway__btn developer-gateway__btn--primary"
              :disabled="starting"
              @click="startDeveloperServer"
            >
              {{ starting ? "Starting..." : "Start Dev Server" }}
            </button>
            <button
              v-else-if="hasUdevRepo"
              class="developer-gateway__btn developer-gateway__btn--primary"
              @click="openDeveloper"
            >
              Open Developer
            </button>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { SNACKBAR_BASE } from "@/api/base";

const DEV_SURFACE_URL = "http://localhost:5176";

const starting = ref(false);
const refreshing = ref(false);
const hasUdevRepo = ref(false);
const status = reactive({
  active: false,
  message: "Checking developer server...",
});

async function refreshRepoAvailability() {
  try {
    const res = await fetch(`${SNACKBAR_BASE}/api/developer/repos?scope=all`, {
      signal: AbortSignal.timeout(4000),
    });
    if (!res.ok) {
      hasUdevRepo.value = false;
      return;
    }
    const payload = await res.json();
    const repos = Array.isArray(payload?.repos) ? payload.repos : [];
    hasUdevRepo.value = repos.some(
      (repo: any) => String(repo?.name || "").toLowerCase() === "udev",
    );
  } catch {
    hasUdevRepo.value = false;
  }
}

async function refreshStatus() {
  refreshing.value = true;
  try {
    await refreshRepoAvailability();
    const res = await fetch(`${SNACKBAR_BASE}/api/developer/status`, {
      signal: AbortSignal.timeout(3000),
    });
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    const data = await res.json();
    status.active = Boolean(data?.active);
    if (!hasUdevRepo.value) {
      status.message = "uDev repository not found under ~/Code.";
      return;
    }
    status.message = status.active
      ? "Developer server is reachable on localhost:5176."
      : "Developer server is not running yet.";
  } catch (error: any) {
    status.active = false;
    status.message =
      error?.message || "Unable to reach developer status endpoint.";
  } finally {
    refreshing.value = false;
  }
}

async function startDeveloperServer() {
  starting.value = true;
  try {
    const res = await fetch(`${SNACKBAR_BASE}/api/developer/start`, {
      method: "POST",
      signal: AbortSignal.timeout(8000),
    });
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }

    // Give Vite a short boot window, then re-check.
    setTimeout(() => {
      void refreshStatus();
    }, 1500);
  } catch (error: any) {
    status.message = error?.message || "Failed to start developer server.";
  } finally {
    starting.value = false;
  }
}

function openDeveloper() {
  window.location.href = DEV_SURFACE_URL;
}

onMounted(() => {
  void refreshRepoAvailability().then(() => {
    void refreshStatus();
  });
});
</script>

<style scoped>
.developer-gateway {
  max-width: calc(var(--usx-touch-min) * 16);
  margin: 0 auto;
  padding: var(--usx-spacing-xl);
}

.developer-gateway__header {
  margin-bottom: var(--usx-spacing-lg);
}

.developer-gateway__title {
  margin: 0 0 var(--usx-spacing-xs);
  font-size: var(--usx-font-size-2xl);
  color: var(--usx-color-on-surface);
}

.developer-gateway__subtitle {
  margin: 0;
  color: var(--usx-color-on-surface-muted);
}

.developer-gateway__card {
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-lg);
  background: var(--usx-color-surface);
  padding: var(--usx-spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-md);
}

.developer-gateway__status-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--usx-spacing-sm);
}

.developer-gateway__status-label {
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
}

.developer-gateway__status-value {
  font-size: var(--usx-font-size-base);
}

.developer-gateway__status-value--online {
  color: var(--usx-color-success);
}

.developer-gateway__status-value--offline {
  color: var(--usx-color-warning);
}

.developer-gateway__message {
  margin: 0;
  color: var(--usx-color-on-surface);
}

.developer-gateway__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--usx-spacing-sm);
}

.developer-gateway__btn {
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  background: var(--usx-color-surface-variant);
  color: var(--usx-color-on-surface);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  cursor: pointer;
}

.developer-gateway__btn:disabled {
  opacity: 0.7;
  cursor: default;
}

.developer-gateway__btn--primary {
  border-color: var(--usx-color-primary);
  color: var(--usx-color-primary);
}
</style>

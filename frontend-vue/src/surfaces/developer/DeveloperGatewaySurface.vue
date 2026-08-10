<template>
  <div class="surface">
    <div class="surface__content">
      <div class="developer-gateway" aria-label="developer-server-splash">
        <section class="developer-gateway__card">
          <span class="developer-gateway__badge">Developer Surface</span>
          <h1 class="developer-gateway__title">{{ splashTitle }}</h1>
          <p class="developer-gateway__message">{{ status.message }}</p>

          <div
            class="developer-gateway__meter"
            :class="{
              'developer-gateway__meter--active':
                starting || refreshing || status.active,
            }"
          >
            <span class="developer-gateway__meter-bar" />
          </div>

          <div class="developer-gateway__actions">
            <button
              class="developer-gateway__btn"
              :disabled="starting || refreshing || autoStarting"
              @click="refreshStatus(false)"
            >
              {{ refreshing ? "Checking..." : "Refresh" }}
            </button>
            <button
              v-if="hasUdevRepo && !status.active && autoStartFailed"
              class="developer-gateway__btn developer-gateway__btn--primary"
              :disabled="starting || autoStarting"
              @click="ensureDeveloperRunning"
            >
              {{ starting || autoStarting ? "Starting..." : "Retry Start" }}
            </button>
            <button
              v-else-if="hasUdevRepo"
              class="developer-gateway__btn developer-gateway__btn--primary"
              :disabled="autoOpening"
              @click="openDeveloper"
            >
              {{ autoOpening ? "Opening..." : "Open Developer" }}
            </button>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { SNACKBAR_BASE } from "@/api/base";

const DEV_SURFACE_URL = "http://localhost:5176";

const starting = ref(false);
const refreshing = ref(false);
const hasUdevRepo = ref(false);
const autoOpening = ref(false);
const hasAutoOpened = ref(false);
const autoStarting = ref(false);
const autoStartFailed = ref(false);
const status = reactive({
  active: false,
  message: "Checking developer server...",
});

const splashTitle = computed(() => {
  if (starting.value || autoStarting.value) return "Starting Developer Surface";
  if (refreshing.value) return "Checking Dev Mode";
  if (status.active) return "Developer Surface Ready";
  if (autoStartFailed.value) return "Dev Mode Start Failed";
  return "Starting Dev Mode";
});

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function checkDeveloperStatus(): Promise<boolean> {
  const res = await fetch(`${SNACKBAR_BASE}/api/developer/status`, {
    signal: AbortSignal.timeout(3000),
  });
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`);
  }
  const data = await res.json();
  return Boolean(data?.active);
}

function autoAdvanceIfReady() {
  if (!status.active || hasAutoOpened.value) return;
  hasAutoOpened.value = true;
  autoOpening.value = true;
  setTimeout(() => {
    openDeveloper();
  }, 700);
}

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

async function refreshStatus(allowAutoStart = true) {
  refreshing.value = true;
  try {
    await refreshRepoAvailability();
    status.active = await checkDeveloperStatus();
    if (!hasUdevRepo.value) {
      status.message = "uDev repository not found under ~/Code.";
      return;
    }
    status.message = status.active
      ? "Developer server is reachable on localhost:5176."
      : allowAutoStart
        ? "Starting developer server..."
        : "Developer server is not running yet.";

    if (!status.active && allowAutoStart) {
      await ensureDeveloperRunning();
      return;
    }

    autoAdvanceIfReady();
  } catch (error: any) {
    status.active = false;
    status.message =
      error?.message || "Unable to reach developer status endpoint.";
  } finally {
    refreshing.value = false;
  }
}

async function ensureDeveloperRunning() {
  if (starting.value || autoStarting.value) return;
  autoStarting.value = true;
  autoStartFailed.value = false;
  hasAutoOpened.value = false;
  status.message = "Starting developer server...";
  try {
    const started = await startDeveloperServer();
    if (!started) {
      autoStartFailed.value = true;
      status.message =
        "Unable to auto-start developer server. Use Retry Start.";
    }
  } finally {
    autoStarting.value = false;
  }
}

async function startDeveloperServer() {
  starting.value = true;
  hasAutoOpened.value = false;
  try {
    const res = await fetch(`${SNACKBAR_BASE}/api/developer/start`, {
      method: "POST",
      signal: AbortSignal.timeout(8000),
    });
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }

    // Wait for Vite to become reachable and then auto-open.
    for (let i = 0; i < 10; i++) {
      await sleep(700);
      try {
        status.active = await checkDeveloperStatus();
      } catch {
        status.active = false;
      }
      if (status.active) {
        status.message = "Developer server is reachable on localhost:5176.";
        autoAdvanceIfReady();
        return true;
      }
    }
    return false;
  } catch (error: any) {
    status.message = error?.message || "Failed to start developer server.";
    return false;
  } finally {
    starting.value = false;
  }
}

function openDeveloper() {
  window.location.href = DEV_SURFACE_URL;
}

onMounted(() => {
  void refreshStatus(true);
});
</script>

<style scoped>
.developer-gateway {
  max-width: calc(var(--usx-touch-min) * 14);
  margin: 0 auto;
  padding: var(--usx-spacing-2xl) var(--usx-spacing-xl);
}

.developer-gateway__title {
  margin: 0;
  font-size: var(--usx-font-size-2xl);
  color: var(--usx-color-on-surface);
}

.developer-gateway__card {
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-lg);
  background: var(--usx-color-surface);
  padding: var(--usx-spacing-xl);
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-lg);
}

.developer-gateway__badge {
  align-self: flex-start;
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-xs);
  font-family: var(--usx-font-family-mono);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  background: var(--usx-color-surface-variant);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-full);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
}

.developer-gateway__message {
  margin: 0;
  color: var(--usx-color-on-surface-muted);
}

.developer-gateway__meter {
  width: 100%;
  height: var(--usx-spacing-sm);
  border-radius: var(--usx-radius-full);
  background: var(--usx-color-surface-variant);
  overflow: hidden;
}

.developer-gateway__meter-bar {
  display: block;
  width: 28%;
  height: 100%;
  border-radius: var(--usx-radius-full);
  background: var(--usx-color-primary);
  transform: translateX(-120%);
}

.developer-gateway__meter--active .developer-gateway__meter-bar {
  animation: developer-gateway-slide 1600ms ease-in-out infinite;
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

@keyframes developer-gateway-slide {
  0% {
    transform: translateX(-120%);
  }
  50% {
    transform: translateX(120%);
  }
  100% {
    transform: translateX(280%);
  }
}
</style>

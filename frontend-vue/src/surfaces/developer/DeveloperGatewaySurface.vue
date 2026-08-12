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
              'developer-gateway__meter--active': status.active,
            }"
          >
            <span class="developer-gateway__meter-bar" />
          </div>

          <div class="developer-gateway__actions">
            <button
              class="developer-gateway__btn developer-gateway__btn--primary"
              :disabled="!hasUdevRepo"
              @click="openDeveloper"
            >
              Open Repo Browser
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

const hasUdevRepo = ref(false);
const status = reactive({
  active: false,
  message: "Checking repositories...",
});

const splashTitle = computed(() => {
  if (status.active) return "Developer Surface Ready";
  if (hasUdevRepo.value) return "Repositories Found";
  return "Repo Browser";
});

async function refreshRepoAvailability() {
  try {
    const res = await fetch(`${SNACKBAR_BASE}/api/developer/repos`, {
      signal: AbortSignal.timeout(4000),
    });
    if (res.ok) {
      const payload = await res.json();
      const repos = Array.isArray(payload?.repos) ? payload.repos : [];
      hasUdevRepo.value = repos.length > 0;
      status.message = repos.length > 0
        ? `${repos.length} repos found.`
        : "No repositories found under ~/Code/.";
    } else {
      hasUdevRepo.value = false;
      status.message = "Repo API unavailable.";
    }
  } catch {
    hasUdevRepo.value = false;
    status.message = "Repo API unavailable.";
  }
}

function openDeveloper() {
  window.open('/developer?tab=repository', '_top');
}

onMounted(() => {
  void refreshRepoAvailability();
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

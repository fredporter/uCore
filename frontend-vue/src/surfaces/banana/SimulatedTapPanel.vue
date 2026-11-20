<template>
  <details class="surface__panel tap-panel">
    <summary>Simulated NFC tap</summary>
    <form class="tap-panel__form" @submit.prevent="runTap(false)">
      <label>
        Marker ID
        <input v-model.trim="marker" maxlength="128" required autocomplete="off" />
      </label>
      <div class="tap-panel__actions">
        <button class="usx-btn" type="submit" :disabled="pending || !identity.activeProfileId">
          <UIcon name="nfc" /> Simulate tap
        </button>
        <button
          class="usx-btn" type="button"
          :disabled="pending || !lastEvent || lastEvent.marker !== marker || !identity.activeProfileId"
          @click="runTap(true)"
        >
          <UIcon name="replay" /> Replay tap
        </button>
      </div>
    </form>

    <p v-if="!identity.activeProfileId">Choose a local user profile to simulate a tap.</p>
    <p v-if="error" role="alert">{{ error }}</p>
    <div v-if="receipt" aria-live="polite">
      <p>{{ receipt.replayed ? "Replayed tap" : "Tap resolved" }}</p>
      <dl>
        <dt>Event</dt>
        <dd>{{ receipt.event_id }}</dd>
        <dt>Waypoint</dt>
        <dd>{{ receipt.waypoint_ref }}</dd>
        <template v-if="receipt.registered_position">
          <dt>Registered coordinates</dt>
          <dd>{{ receipt.registered_position.lat }}°, {{ receipt.registered_position.lon }}°</dd>
        </template>
        <dt>Observed position</dt>
        <dd>Unknown</dd>
      </dl>
      <ul v-if="receipt.authorised_resource_refs.length" aria-label="Available fixture resources">
        <li v-for="resource in receipt.authorised_resource_refs" :key="resource">{{ resource }}</li>
      </ul>
      <p v-else>No available fixture resources at this waypoint.</p>
    </div>
  </details>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import { ucoreApi } from "../../api/client";
import UIcon from "../../skills/atoms/UIcon.vue";
import { useIdentityStore } from "../../stores/identity";

const identity = useIdentityStore();
const marker = ref("marker-oakhaven-nfc-01");
const pending = ref(false);
const error = ref("");
const receipt = ref<Awaited<ReturnType<typeof ucoreApi.spatial.simulateTap>>["data"] | null>(null);
const lastEvent = ref<{ id: string; marker: string } | null>(null);

watch([() => identity.activeProfileId, marker], () => {
  error.value = "";
  receipt.value = null;
  lastEvent.value = null;
});

async function runTap(replay: boolean) {
  const profile = identity.activeProfileId;
  if (pending.value || !profile || !marker.value) return;

  pending.value = true;
  error.value = "";
  receipt.value = null;
  try {
    const event = (replay && lastEvent.value) || {
      id: Array.from(globalThis.crypto.getRandomValues(new Uint8Array(16)),
        (byte) => byte.toString(16).padStart(2, "0")).join(""),
      marker: marker.value,
    };
    lastEvent.value = event;
    const result = await ucoreApi.spatial.simulateTap({
      event_id: event.id,
      marker_envelope: { version: "1.0", marker_id: event.marker },
    });
    if (lastEvent.value !== null && lastEvent.value.id === event.id && identity.activeProfileId === profile) {
      if (result.ok) receipt.value = result.data;
      else if (result.status === 401) error.value = "Choose a local user profile to simulate a tap.";
      else if (result.status === 403) error.value = "This waypoint is unavailable.";
      else if (result.status === 400) error.value = "Enter a valid marker ID.";
      else error.value = "The tap could not be resolved.";
    }
  } catch {
    if (identity.activeProfileId === profile) error.value = "The local tap service is unavailable.";
  } finally {
    pending.value = false;
  }
}
</script>

<style scoped>
.tap-panel {
  margin: 0;
  min-width: 0;
  padding: var(--usx-spacing-md);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  background: var(--usx-color-surface);
}
summary { cursor: pointer; }
.tap-panel__form, label { display: grid; gap: var(--usx-spacing-sm); }
.tap-panel__form { margin-block: var(--usx-spacing-sm); }
input {
  max-width: 24rem;
  padding: var(--usx-spacing-sm);
  color: var(--usx-color-on-surface);
  background: var(--usx-color-surface);
}
.tap-panel__actions { display: flex; flex-wrap: wrap; gap: var(--usx-spacing-sm); }
.tap-panel dl {
  display: grid;
  gap: var(--usx-spacing-xs);
}
.tap-panel dd { margin: 0 0 var(--usx-spacing-sm); }
dd, li { overflow-wrap: anywhere; }
</style>

import { defineStore } from "pinia";
import { computed, ref } from "vue";
import { UCORE_BASE } from "../api/base";

export interface UserIdentity {
  user_id: string;
  codeword: string;
  install_id: string;
  session_id: string;
}

export const useIdentityStore = defineStore("identity", () => {
  const identity = ref<UserIdentity | null>(null);
  const loading = ref(false);
  const error = ref("");
  const authenticated = computed(() => Boolean(identity.value?.user_id));
  const displayName = computed(() => identity.value?.codeword || identity.value?.user_id || "Local user");
  const initials = computed(() => displayName.value.slice(0, 2).toUpperCase());

  async function load() {
    loading.value = true;
    error.value = "";
    try {
      const response = await fetch(`${UCORE_BASE}/api/identity/me`, { signal: AbortSignal.timeout(3000) });
      if (!response.ok) throw new Error(`Identity returned ${response.status}`);
      identity.value = await response.json();
    } catch (exc) {
      identity.value = null;
      error.value = exc instanceof Error ? exc.message : "Identity unavailable";
    } finally {
      loading.value = false;
    }
  }

  return { identity, loading, error, authenticated, displayName, initials, load };
});

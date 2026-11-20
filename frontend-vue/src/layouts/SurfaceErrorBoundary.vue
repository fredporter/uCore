<template>
  <RecoverySurface v-if="failed" unavailable @retry="failed = false" />
  <slot v-else />
</template>

<script setup lang="ts">
import { onErrorCaptured, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import RecoverySurface from '../surfaces/recovery/RecoverySurface.vue';

const route = useRoute();
const failed = ref(false);

watch(() => route.fullPath, () => { failed.value = false; });

onErrorCaptured((error) => {
  console.error('uCore surface failed to load', error);
  failed.value = true;
  return false;
});
</script>

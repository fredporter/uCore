<template>
  <div class="surface" :class="{'surface--tab-nav-vertical':shell.tabOrientation==='vertical'}">
    <SurfaceTabNav :model-value="tab" :tabs="tabs" :orientation="shell.tabOrientation" @update:model-value="router.replace({query:{tab:$event}})" @toggle-orientation="shell.toggleTabOrientation()" />
    <div class="surface__content"><SnackbarDashboardPanel v-if="tab==='dashboard'" /><SnackbarServicesPanel v-else-if="tab==='services'" /><SnackbarLogsPanel v-else /></div>
  </div>
</template>
<script setup lang="ts">
import { computed, onMounted, onBeforeUnmount } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useShellStore } from '../../stores/shell';
import { useSnackbarOpsStore } from '../../stores/snackbarOps';
import SurfaceTabNav from '../../skills/molecules/SurfaceTabNav.vue';
import SnackbarDashboardPanel from '../snackbar/panels/SnackbarDashboardPanel.vue';
import SnackbarServicesPanel from '../snackbar/panels/SnackbarServicesPanel.vue';
import SnackbarLogsPanel from '../snackbar/panels/SnackbarLogsPanel.vue';
const shell=useShellStore(), srv=useSnackbarOpsStore(),route=useRoute(),router=useRouter();
const tabs=[{id:'dashboard',label:'Server',icon:'dns'},{id:'services',label:'Services',icon:'settings_applications'},{id:'logs',label:'Logs',icon:'receipt_long'}];
const tab=computed(()=>tabs.some(t=>t.id===route.query.tab)?String(route.query.tab):'dashboard');
onMounted(()=>{void srv.fetchHealth();void srv.fetchUnifiedServices();void srv.fetchLogs();srv.startHealthPolling(15000);});
onBeforeUnmount(()=>srv.stopHealthPolling());
</script>

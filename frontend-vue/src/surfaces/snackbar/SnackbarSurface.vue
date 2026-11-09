<template>
  <div class="surface" :class="{'surface--tab-nav-vertical':shell.tabOrientation==='vertical'}">
    <SurfaceTabNav :model-value="tab" :tabs="tabs" :orientation="shell.tabOrientation" @update:model-value="router.replace({query:{tab:$event}})" @toggle-orientation="shell.toggleTabOrientation()" />
    <div class="surface__content snackbar-content">
      <template v-if="tab==='dashboard'"><header><h2>Snackbar</h2><p>Connected apps, local collections and useful routines.</p></header><SnackbarSyncPanel /><RouterLink class="usx-btn" to="/system?tab=apps">Manage apps</RouterLink><RouterLink class="usx-btn" to="/workflow">Open Workflow</RouterLink></template>
      <ConnectionsPanel v-else-if="['tasks','contacts','notes'].includes(tab)" :key="tab" collection-only :initial-kind="tab" />
      <FeedsPanel v-else-if="tab==='feeds'" />
      <template v-else-if="tab==='snacks'"><SnackbarSnacksPanel /><details><summary>Available skills</summary><SnackbarSkillsPanel /></details></template>
      <SnackbarFeedsPanel v-else-if="tab==='automation'" />
      <LocalAssistantPanel v-else-if="tab==='ai'" />
      <SnackbarLogsPanel v-else-if="tab==='logs'" />
    </div>
  </div>
</template>
<script setup lang="ts">
import { computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useShellStore } from '../../stores/shell';
import { useSnackbarOpsStore } from '../../stores/snackbarOps';
import SurfaceTabNav from '../../skills/molecules/SurfaceTabNav.vue';
import SnackbarSyncPanel from '../../skills/molecules/SnackbarSyncPanel.vue';
import ConnectionsPanel from '../system/ConnectionsPanel.vue';
import FeedsPanel from '../workflow/panels/FeedsPanel.vue';
import SnackbarSnacksPanel from './panels/SnackbarSnacksPanel.vue';
import SnackbarSkillsPanel from './panels/SnackbarSkillsPanel.vue';
import SnackbarFeedsPanel from './panels/SnackbarFeedsPanel.vue';
import LocalAssistantPanel from './panels/LocalAssistantPanel.vue';
import SnackbarLogsPanel from './panels/SnackbarLogsPanel.vue';
const shell=useShellStore(),srv=useSnackbarOpsStore(),route=useRoute(),router=useRouter();
const tabs=[{id:'dashboard',label:'Snackbar',icon:'storefront'},{id:'tasks',label:'Tasks',icon:'sync'},{id:'contacts',label:'Contacts',icon:'contacts'},{id:'notes',label:'Notes',icon:'description'},{id:'feeds',label:'Feeds',icon:'rss_feed'},{id:'snacks',label:'Snacks',icon:'restaurant_menu'},{id:'automation',label:'Routines',icon:'auto_mode'},{id:'ai',label:'Assistant',icon:'chat'}];
const tab=computed(()=>tabs.some(t=>t.id===route.query.tab)?String(route.query.tab):route.query.tab==='logs'?'logs':'dashboard');
watch(()=>route.query.tab,value=>{if(value==='services')void router.replace('/server?tab=services');if(['skills','extensions'].includes(String(value)))void router.replace('/snackbar?tab=snacks');},{immediate:true});
watch(tab,value=>{if(value==='snacks')void srv.fetchExecutables();if(value==='logs')void srv.fetchLogs();},{immediate:true});
</script>
<style scoped>
.snackbar-content { padding:var(--usx-spacing-md); }
h2 { font-size:var(--usx-font-size-xl); }
header p { color:var(--usx-color-on-surface-muted); }
</style>

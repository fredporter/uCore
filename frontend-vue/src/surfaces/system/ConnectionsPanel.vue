<template>
  <section class="connections">
    <header v-if="!connectionsOnly"><div><h2>{{ collectionOnly ? names[activeKind] : 'Connections' }}</h2><p>{{ collectionOnly ? 'Your combined local collection. Connections and source IDs stay linked when you edit.' : 'Your local collection, connected to the accounts and lists you choose.' }}</p></div><div class="connection-actions"><button v-if="collectionOnly" class="usx-btn" @click="router.push('/system?tab=connections')">Connections</button><button class="usx-btn" :disabled="busy" @click="load">Refresh</button></div></header>
    <p v-if="collectionOnly && error" role="alert">{{ error }}</p>
    <template v-if="!collectionOnly">
    <p v-if="authUrl"><a :href="authUrl" target="_blank" rel="noopener noreferrer">Open Google sign-in in your system browser</a></p>
    <p v-if="error" role="alert">{{ error }}</p><p v-if="notice" role="status">{{ notice }}</p>
    <section v-if="!state.setup?.completed && !connectionsOnly" class="connection-box"><h3>Set up your workspace</h3><p>A short story will guide your profile, local settings and account choices.</p><button class="usx-btn usx-btn--primary" @click="router.push('/setup')">Start User Setup</button></section>
    <div class="connection-actions"><button v-if="state.providers?.apple?.available && providerMode!=='cloud'" class="usx-btn" :disabled="busy" @click="add('apple')"><UIcon name="computer" />Connect local Mac apps</button><button v-if="providerMode!=='local'" class="usx-btn" :disabled="busy" @click="add('google')"><UIcon name="cloud" />Add Google account</button></div>
    <details v-for="(provider,id) in visibleProviders" :key="id" class="connection-capabilities">
      <summary>{{ id === 'apple' ? 'Apple' : 'Google' }} adapter capabilities</summary>
      <p>Code support only. Connection, consent and permissions are required; live qualification is pending.</p>
      <p v-if="id === 'google' && provider.direct_access_allowed === false">Direct Google access is unavailable for this profile. Drone access is unavailable.</p>
      <p v-if="!provider.capabilities.adapter_available">Unavailable on this host.</p>
      <dl><template v-for="(capability,kind) in provider.capabilities.collections" :key="kind"><dt>{{ names[String(kind)] }}</dt><dd>{{ capability.read ? 'Read' : 'Read unavailable' }} · {{ capability.create ? 'Create' : 'Create unavailable' }} · {{ capability.update ? 'Update' : 'Update unavailable' }} · Delete unavailable<p>{{ capability.limitations }}</p></dd></template></dl>
    </details>
    <article v-for="connection in visibleConnections" :key="connection.id" :id="'connection-'+connection.id" class="connection-feed__entry">
      <header><h3>{{ connection.provider === 'apple' ? 'Apple on this Mac' : (connection.health.account || 'Google account') }} </h3><span>{{ healthLabel(connection.health.state) }}</span></header>
      <p v-if="connection.health.error" role="status">{{ connection.health.error }}</p>
      <small v-if="connection.health.last_success">Last successful sync: {{ new Date(connection.health.last_success).toLocaleString() }} · {{ connection.health.pulled || 0 }} new · {{ connection.health.updated || 0 }} updated · {{ connection.health.pushed || 0 }} pushed</small>
      <button class="usx-btn" @click="browseAccount(connection)"><UIcon name="folder_open" />Browse synced records</button>
      <details class="connection-feed__settings"><summary>Connection settings</summary>
      <p v-if="connection.provider==='apple'">Connects to the apps on this Mac. Google accounts configured in macOS Internet Accounts can be included. macOS manages iCloud and account sync.</p><fieldset :disabled="busy || !adapterAvailable(connection)"><legend>Collections</legend><label v-for="kind in kinds" :key="kind" class="inline"><input type="checkbox" :checked="!!connection.config.collections[kind]" @change="toggleKind(connection,kind,($event.target as HTMLInputElement).checked)" />{{ names[kind] }}</label></fieldset>
      <p v-if="connection.provider === 'google' && state.google_auth_configured===false">Direct Google sign-in needs a one-time device setup. Local Mac app connections do not require it.</p>
      <p v-if="connection.provider === 'google'">Direct cloud mode: sign in, then choose lists. Records are stored locally. Drive notes use Markdown files, not Google Keep.</p>
      <div class="connection-actions"><button v-if="connection.provider === 'google'" class="usx-btn" :disabled="busy || !adapterAvailable(connection)" @click="authorize(connection)">Choose Google account</button><button class="usx-btn" :disabled="busy || !adapterAvailable(connection)" @click="discover(connection)">Choose lists and folders</button></div>
      <div v-for="(scope,kind) in connection.config.collections" :key="kind" class="connection-scope">
        <h4>{{ names[String(kind)] }}</h4>
        <label v-for="list in discoveries[connection.id]?.[kind] || []" :key="list.id" class="inline"><input type="checkbox" v-model="scope.lists" :value="list.id" />{{ list.title }}</label>
        <p v-if="!discoveries[connection.id]?.[kind]">{{ scope.lists.length }} lists selected. Use “Choose lists and folders” to change them.</p>
<label v-if="String(kind) === 'tasks'">Local task list (optional)<input v-model="scope.local_list" placeholder="Keep source list names" /></label>
        <label>Records<select v-model="scope.filter"><option value="all">All in selected lists</option><option v-if="String(kind) === 'mail'" value="flagged">Colour-flagged only</option><option v-if="connection.provider === 'google' && ['contacts','notes','mail'].includes(String(kind))" value="starred">Starred only</option><option v-if="connection.provider === 'apple' && String(kind) === 'contacts'" value="vip">VIP group only</option></select></label>
        <label v-if="scope.filter === 'vip'">VIP group<select v-model="scope.vip_group"><option value="">Choose a group</option><option v-for="list in discoveries[connection.id]?.contacts || []" :key="list.id" :value="list.id">{{ list.title }}</option></select></label>
        <p v-if="scope.filter === 'vip'">Choose the Contacts group you use for VIPs. Apple Mail VIP is separate from a coloured flag and is not inferred.</p>
        <label v-if="String(kind)!=='tasks'">Flag automation<select v-model="scope.flag_action"><option value="">Keep flags as information</option><option value="create-task">Create one linked task when flagged, starred, or VIP</option></select></label><label v-if="scope.flag_action==='create-task'">Task list for flagged items<input v-model="scope.flag_task_list" placeholder="inbox" /></label>
        <label>Direction<select v-model="scope.direction"><option value="pull">Pull into local collection</option><option value="both">Push and pull</option></select></label>
        <label v-if="scope.direction === 'both'">Destination for records you share<select v-model="scope.target"><option value="">Choose destination</option><option v-for="list in discoveries[connection.id]?.[kind] || []" :key="list.id" :value="list.id" :disabled="list.writable===false">{{ list.title }}</option></select></label>
        <p v-if="String(kind) === 'mail'">Mail shares flags and read state on linked messages. It does not send or copy messages between accounts.</p>
        <fieldset v-if="connection.provider === 'google' && String(kind) === 'mail'"><legend>Flag colours → Gmail labels</legend><label v-for="colour in colours" :key="colour">{{ colour }}<select v-model="scope.flag_labels[colour]"><option value="">No mapping</option><option v-for="list in (discoveries[connection.id]?.mail || []).filter((label:any)=>label.type==='user')" :key="list.id" :value="list.id">{{ list.title }}</option></select></label></fieldset>
        <label>Selection<select v-model="scope.selection"><option value="all">All matching records</option><option value="records">Choose individual records</option></select></label>
        <button v-if="scope.selection === 'records'" class="usx-btn" :disabled="busy || !adapterAvailable(connection) || !scope.lists.length" @click="preview(connection,String(kind))">Choose individual records</button><small>{{ scope.records?.length || 'All matching' }} records selected</small>
        <div v-if="previews[connection.id]?.[kind]" class="connection-preview"><label v-for="item in previews[connection.id][kind]" :key="item.id" class="inline"><input type="checkbox" v-model="scope.records" :value="item.id" />{{ item.data.title }}</label></div>
      </div>
      <div class="connection-actions"><label class="inline"><input type="checkbox" v-model="connection.config.enabled" />Sync automatically</label><label>Every <input type="number" min="60" max="86400" v-model.number="connection.config.interval" /> seconds</label><button class="usx-btn" :disabled="busy" @click="saveConnection(connection)">Save connection</button><button class="usx-btn" :disabled="busy || !adapterAvailable(connection)" @click="sync(connection)">Sync now</button><button class="usx-btn" :disabled="busy" @click="disconnect(connection)">Disconnect</button></div>
      </details>
    </article>
    <form v-if="state.setup?.completed && !connectionsOnly" class="connection-box" @submit.prevent="completeSetup"><h3>Your profile</h3><label>Name<input v-model="displayName" required /></label><label>Your contact card<select v-model="state.setup.self_contact"><option value="">Choose after importing contacts</option><option v-for="contact in allRecords.filter(r=>r.kind==='contacts')" :key="contact.id" :value="contact.id">{{ contact.data.title }}</option></select></label><button class="usx-btn" :disabled="busy">Save profile</button></form>
    <section v-if="state.pending_exports?.length" class="connection-box"><h3>Check an interrupted export</h3><p>An earlier create did not return a confirmed result. To avoid duplicates, find the record at its destination and link it before retrying.</p><div v-for="pending in state.pending_exports" :key="pending.connection+pending.record"><p>{{ recordTitle(pending.record) }}</p><button class="usx-btn" @click="previewPending(pending)">Find destination record</button><label v-if="pendingChoices[pending.record]">Destination record<select v-model="pendingRemote[pending.record]"><option value="">Choose the matching record</option><option v-for="remote in pendingChoices[pending.record]" :key="remote.id" :value="remote.id">{{ remote.data.title }}</option></select></label><button v-if="pendingRemote[pending.record]" class="usx-btn" @click="linkPending(pending)">Link and review differences</button></div></section>
    </template>
    <section v-if="!connectionsOnly" class="connection-box"><h3 v-if="!collectionOnly">Your collection</h3><div class="connection-actions" role="group" aria-label="Collection type"><button v-for="kind in (collectionOnly ? [] : kinds)" :key="kind" class="usx-btn" :aria-pressed="activeKind === kind" @click="activeKind=kind; loadRecords()">{{ names[kind] }} {{ state.counts?.[kind] || 0 }}</button><button v-if="!account" class="usx-btn" @click="newRecord">New record</button></div>
      <p v-if="account">Synced records for {{ accountLabel }}. These snapshots are read-only.</p>
      <p v-if="account && !records.length && !busy && !error">No synced records in this collection.</p>
      <p v-if="!account && !records.length && !busy">No {{ names[activeKind].toLowerCase() }} yet. Create a record here or choose source lists in Connections.</p>
      <ul v-if="account"><li v-for="record in records" :key="record.id">{{ record.data.title || 'Untitled record' }}</li></ul>
      <template v-else><button v-for="record in records" :key="record.id" class="usx-btn collection-row" @click="openRecord(record)"><span>{{ record.data.title }}</span><small>{{ (record.data.flags || []).join(' · ') }} {{ record.data.starred ? 'Starred' : '' }} {{ record.data.vip ? 'VIP' : '' }}</small></button></template>
    </section>
    <form v-if="edit && !connectionsOnly && !account" class="connection-box" @submit.prevent="saveRecord"><h3>{{ edit.id ? 'Edit record' : 'New record' }}</h3><button v-if="edit.kind==='notes' && edit.file_path" type="button" class="usx-btn" @click="openInEditor(edit)">Open in Editor</button><p v-if="edit.sources?.length">Connected copies: {{ edit.sources.map((source:any)=>source.account || source.provider).join(' · ') }}</p><details v-if="edit.data.alternatives"><summary>Other preserved values</summary><dl><template v-for="(value,key) in edit.data.alternatives" :key="key"><dt>{{ key }}</dt><dd>{{ displayValue(value) }}</dd></template></dl></details><label>Title<input v-model="edit.data.title" required /></label><label>Notes<textarea v-model="edit.data.body" rows="5" /></label><label v-if="edit.kind==='tasks'">Status<select v-model="edit.data.status"><option value="todo">Open</option><option value="completed">Done</option></select></label><label v-if="edit.kind==='tasks'">Due<input type="datetime-local" :value="localDate(edit.data.due)" @change="edit.data.due=isoDate(($event.target as HTMLInputElement).value)" /></label><label v-if="edit.kind==='calendar'">Starts<input type="datetime-local" required :value="localDate(edit.data.start?.dateTime || edit.data.start?.date)" @change="edit.data.start={dateTime:isoDate(($event.target as HTMLInputElement).value)}" /></label><label v-if="edit.kind==='calendar'">Ends<input type="datetime-local" required :value="localDate(edit.data.end?.dateTime || edit.data.end?.date)" @change="edit.data.end={dateTime:isoDate(($event.target as HTMLInputElement).value)}" /></label><label v-if="edit.kind==='contacts'">Emails (one per line)<textarea v-model="emails" rows="2" /></label><label v-if="edit.kind==='contacts'">Phones (one per line)<textarea v-model="phones" rows="2" /></label>
      <fieldset><legend>Flags</legend><label v-for="colour in colours" :key="colour" class="inline"><input type="checkbox" v-model="edit.data.flags" :value="colour" />{{ colour }}</label><label class="inline"><input type="checkbox" v-model="edit.data.starred" />Starred</label><label class="inline"><input type="checkbox" v-model="edit.data.vip" />VIP</label></fieldset>
      <fieldset><legend>Share with these connections</legend><label v-for="connection in state.connections.filter((c:any)=>c.config.collections[edit.kind]?.direction==='both')" :key="connection.id" class="inline"><input type="checkbox" v-model="edit.data.destinations" :value="connection.id" />{{ connection.provider }} {{ connection.id.slice(0,6) }}</label></fieldset><p>Unsupported flags stay in your local record. Apple Mail can display one colour flag. Other providers keep their own fields.</p><div class="connection-actions"><button class="usx-btn usx-btn--primary" :disabled="busy">Save</button><button type="button" class="usx-btn" @click="edit=null">Cancel</button></div>
    </form>
    <section v-if="visibleDuplicates.length && !connectionsOnly && !account" class="connection-box"><h3>Possible duplicates</h3><p>Review both records before combining. Matching titles alone do not prove two records are the same.</p><div v-for="pair in visibleDuplicates" :key="pair.left+pair.right" class="duplicate-row"><span>{{ recordTitle(pair.left) }} / {{ recordTitle(pair.right) }} · {{ pair.reason }}</span><button class="usx-btn" @click="reviewPair(pair)">Review</button></div><div v-if="mergePair"><div class="merge-comparison"><article v-for="record in [mergePair.left,mergePair.right]" :key="record.id"><h4>{{ record.data.title }}</h4><p>{{ record.data.body }}</p><p>{{ (record.data.emails || []).join(', ') }}</p><p>{{ (record.data.phones || []).join(', ') }}</p><p>{{ (record.data.flags || []).join(', ') }}</p></article></div><button class="usx-btn" :disabled="busy" @click="mergeRecords">Combine, keeping left preferred values</button><button class="usx-btn" @click="mergePair=null">Cancel</button></div></section>
    <section v-if="visibleConflicts.length && !connectionsOnly && !account" class="connection-box"><h3>Changes need review</h3><article v-for="conflict in visibleConflicts" :key="conflict.connection+conflict.remote"><p>{{ recordTitle(conflict.record) }}</p><dl class="incoming-values"><template v-for="(value,key) in parseIncoming(conflict.incoming)" :key="key"><dt>{{ key }}</dt><dd>{{ displayValue(value) }}</dd></template></dl><button v-for="choice in ['local','remote','combine']" :key="choice" class="usx-btn" @click="resolve(conflict,choice)">{{ choice === 'local' ? 'Keep local' : choice === 'remote' ? 'Use incoming' : 'Combine values' }}</button></article></section>
  </section>
</template>
<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router';
import { computed, nextTick, onMounted, ref, watch } from 'vue';
import { UCORE_BASE } from '../../api/base';
import { useIdentityStore } from '../../stores/identity';
import { useWorkspaceStore } from '../../stores/workspace';
import { useWorkflowStore } from '../../stores/workflow';
import { getEditorSurface } from '../../composables/useEditorSurface';
import UIcon from '../../skills/atoms/UIcon.vue';
const props=withDefaults(defineProps<{collectionOnly?:boolean;connectionsOnly?:boolean;initialKind?:string;providerMode?:'all'|'local'|'cloud'}>(),{collectionOnly:false,connectionsOnly:false,initialKind:'tasks',providerMode:'all'});
const identity=useIdentityStore();
const router=useRouter();
const route=useRoute();
const kinds=['tasks','contacts','notes','calendar','mail'];
const names:Record<string,string>={tasks:'Tasks',contacts:'Contacts',notes:'Notes',calendar:'Calendar',mail:'Mail'};
const colours=['red','orange','yellow','green','blue','purple','grey'];
const state=ref<any>({connections:[],setup:{},counts:{}}), records=ref<any[]>([]), allRecords=ref<any[]>([]);
const discoveries=ref<Record<string,any>>({}), previews=ref<Record<string,any>>({});
const activeKind=ref(props.initialKind), edit=ref<any>(null), emails=ref(''), phones=ref(''), displayName=ref('');
const pendingChoices=ref<Record<string,any[]>>({}), pendingRemote=ref<Record<string,string>>({});
const busy=ref(false), error=ref(''), notice=ref(''), mergePair=ref<any>(null);
const visibleProviders=computed(()=>Object.fromEntries(Object.entries(state.value.providers || {}).filter(([id,provider]:[string,any])=>provider.capabilities && (props.providerMode==='all'||(props.providerMode==='local'?id==='apple':id==='google'))))) as import('vue').ComputedRef<Record<string,any>>;
const visibleConnections=computed(()=>state.value.connections.filter((c:any)=>props.providerMode==='all'||(props.providerMode==='local'?c.provider==='apple':c.provider==='google')));
function adapterAvailable(connection:any):boolean {
  const provider = state.value.providers?.[connection.provider];
  return provider?.capabilities?.adapter_available === true && provider.direct_access_allowed !== false;
}
function healthLabel(value:string){return ({setup_required:'Choose apps and lists',scope_required:'Choose lists',connected:'Up to date',running:'Syncing',conflict:'Review changes',error:'Needs attention',disconnected:'Disconnected'} as Record<string,string>)[value]||value?.replaceAll('_',' ')||'Not connected';}
const visibleDuplicates=computed(()=>(state.value.duplicates || []).filter((pair:any)=>!props.collectionOnly || allRecords.value.find(r=>r.id===pair.left)?.kind===activeKind.value));
const visibleConflicts=computed(()=>(state.value.conflicts || []).filter((conflict:any)=>!props.collectionOnly || allRecords.value.find(r=>r.id===conflict.record)?.kind===activeKind.value));
async function api(path='',body?:any){const profile=identity.activeProfileId; const response=await fetch(`${UCORE_BASE}/api/connections${path}`,{method:body===undefined?'GET':'POST',headers:{'Content-Type':'application/json'},...(body===undefined?{}:{body:JSON.stringify(body)})});if(profile!==identity.activeProfileId)throw Error('Profile changed; reloading connections');if(!response.ok)throw Error((await response.text()).slice(0,300));return response.json();}
async function work(action:()=>Promise<void>){busy.value=true;error.value='';try{await action();}catch(e){error.value=e instanceof Error?e.message:'Connection unavailable';}finally{busy.value=false;}}
const account = computed(() => props.collectionOnly && typeof route.query.account === 'string' ? route.query.account : '');
const accountLabel = computed(() => {
  const connection = state.value.connections.find((item:any) => item.id === account.value);
  return connection?.health?.account || (connection?.provider === 'apple' ? 'Apple on this Mac' : 'the selected account');
});
function browseAccount(connection:any) {
  void router.push({path:'/system', query:{tab:'apps', workspace:'vault', account:connection.id,
    collection:Object.keys(connection.config.collections)[0] || 'tasks'}});
}
async function loadRecords(){
  const scope = account.value ? '?' + new URLSearchParams({account:account.value}) : '';
  allRecords.value=(await api('/records' + scope)).records;
  records.value=allRecords.value.filter(r=>r.kind===activeKind.value);
  state.value.counts=Object.fromEntries(kinds.map(kind=>[kind,allRecords.value.filter(r=>r.kind===kind).length]));
  const selected=records.value.find(r=>r.id===route.query.record);
  if(!account.value && selected && !edit.value)openRecord(selected);
}
async function load(){await work(async()=>{state.value=await api(); displayName.value=state.value.setup.display_name || identity.displayName; if(!props.connectionsOnly)await loadRecords();});}
async function completeSetup(){await work(async()=>{await api('/setup',{display_name:displayName.value,completed:true,self_contact:state.value.setup.self_contact || ''});await identity.load();state.value=await api();});}
async function add(provider:string){await work(async()=>{
 if(provider==='apple'&&!state.value.providers?.apple?.available)throw Error('Local Apple apps require a Mac host');
 let connection=provider==='apple'?state.value.connections.find((c:any)=>c.provider==='apple'):null;
 if(!connection){connection=await api('',{provider,config:{enabled:false,collections:{tasks:{lists:[],direction:'pull',filter:'all',selection:'all',records:[],flag_labels:{}}}}});state.value=await api();}
 await nextTick();document.getElementById('connection-'+connection.id)?.scrollIntoView?.({block:'nearest',behavior:'smooth'});
 if(provider==='apple'){notice.value='Choose the native apps and lists below. macOS manages their cloud accounts.';}
});}
function toggleKind(c:any,kind:string,enabled:boolean){if(enabled)c.config.collections[kind]={lists:[],direction:'pull',filter:'all',selection:'all',records:[],flag_labels:{}};else delete c.config.collections[kind];}
async function saveConnection(c:any){await api('',{id:c.id,provider:c.provider,config:c.config});notice.value='Connection saved';}
async function discover(c:any){await work(async()=>{await saveConnection(c);discoveries.value[c.id]=(await api(`/${c.id}/discover`,{})).collections;for(const [kind,lists] of Object.entries(discoveries.value[c.id]))c.config.collections[kind].list_titles=Object.fromEntries((lists as any[]).map(list=>[list.id,list.title]));});}
async function authorize(c:any){await work(async()=>{await saveConnection(c);const result=await api(`/${c.id}/authorize`,{open_browser:true});notice.value='Open this sign-in link in your system browser, then return and choose lists.';authUrl.value=result.url;});}
const authUrl=ref('');
async function sync(c:any){await work(async()=>{await saveConnection(c);const result=await api(`/${c.id}/sync`,{});notice.value=result.state==='error'?result.error:`Sync: ${result.state}`;state.value=await api();await loadRecords();});}
async function disconnect(c:any){await work(async()=>{await api(`/${c.id}/disconnect`,{});state.value=await api();});}
async function preview(c:any,kind:string){await work(async()=>{await saveConnection(c);previews.value[c.id]||={};previews.value[c.id][kind]=(await api(`/${c.id}/preview`,{kind})).records;});}
function parseIncoming(value:string){try{return JSON.parse(value);}catch{return {};}}
function displayValue(value:any):string{return Array.isArray(value)?value.map(displayValue).join(' · '):value && typeof value==='object'?Object.values(value).map(displayValue).join(' · '):String(value ?? '');}
function localDate(value:string){if(!value)return '';const date=new Date(value);if(Number.isNaN(date.getTime()))return '';return new Date(date.getTime()-date.getTimezoneOffset()*60000).toISOString().slice(0,16);}
function isoDate(value:string){return value?new Date(value).toISOString():'';}
function newRecord(){emails.value='';phones.value='';edit.value={kind:activeKind.value,data:{title:'',body:'',status:'todo',flags:[],labels:[],destinations:[]}};}
function openRecord(record:any){edit.value=JSON.parse(JSON.stringify(record));edit.value.data.flags||=[];edit.value.data.destinations||=[];emails.value=(record.data.emails||[]).join('\n');phones.value=(record.data.phones||[]).join('\n');}
async function openInEditor(record:any){await work(async()=>{const path=record.file_path;await useWorkspaceStore().selectFile({id:path,path,name:record.data.title+'.md',type:'file'});const file=getEditorSurface().currentFile.value;if(!file)throw Error('Note could not be opened');useWorkflowStore().selectFile({id:path,path,filename:file.filename,extension:'md',binder:'',content:file.content,readOnly:false,version:file.version});await router.push({path:'/workflow',query:{tab:'editor',file:path}});});}
async function saveRecord(){await work(async()=>{if(edit.value.kind==='contacts'){edit.value.data.emails=emails.value.split('\n').filter(Boolean);edit.value.data.phones=phones.value.split('\n').filter(Boolean);}await api('/records',edit.value);edit.value=null;state.value=await api();await loadRecords();});}
async function previewPending(pending:any){await work(async()=>{pendingChoices.value[pending.record]=(await api(`/${pending.connection}/preview`,{kind:pending.kind})).records;});}
async function linkPending(pending:any){await work(async()=>{await api(`/${pending.connection}/link`,{record:pending.record,remote:pendingRemote.value[pending.record]});state.value=await api();});}
function recordTitle(id:string){return allRecords.value.find(r=>r.id===id)?.data.title || id;}
function reviewPair(pair:any){mergePair.value={left:allRecords.value.find(r=>r.id===pair.left),right:allRecords.value.find(r=>r.id===pair.right)};}
async function mergeRecords(){await work(async()=>{await api('/records',{merge:{keep:mergePair.value.left.id,other:mergePair.value.right.id}});mergePair.value=null;state.value=await api();await loadRecords();});}
async function resolve(conflict:any,choice:string){await work(async()=>{await api(`/${conflict.connection}/resolve`,{remote:conflict.remote,choice});state.value=await api();await loadRecords();});}
watch(()=>props.initialKind,kind=>{activeKind.value=kind;edit.value=null;void loadRecords();});
watch(()=>identity.activeProfileId,()=>{state.value={connections:[],setup:{}};edit.value=null;discoveries.value={};previews.value={};authUrl.value='';void load();});
onMounted(load);
</script>
<style scoped>
.connections { display:grid; gap:16px; width:min(100%,70rem); margin-inline:auto; padding:16px; font-family:var(--usx-font-family-sans); text-align:left; }
.connections header,.connection-actions { display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:8px; }
.connections h2,.connections h3,.connections h4,.connections p { margin:0; }.connections h2{font-size:var(--usx-font-size-xl);line-height:1.3;}.connections h3{font-size:var(--usx-font-size-lg);line-height:1.3;}.connections h4{font-size:var(--usx-font-size-base);line-height:1.3;}.connections p { color:var(--usx-color-on-surface-muted); line-height:1.5; }
.connection-box,.connection-scope { display:grid; gap:12px; padding:12px; border:1px solid var(--usx-color-border); border-radius:var(--usx-radius-sm); }
.connections label { display:grid; gap:4px; margin:0; font-size:var(--usx-font-size-sm); }.connections label.inline { display:inline-flex; align-items:center; gap:6px; }
.connections fieldset { display:flex; flex-wrap:wrap; gap:8px; margin:0; padding:8px; border:1px solid var(--usx-color-border); }
.connections .usx-btn { flex:0 0 auto; width:auto; justify-self:start; display:inline-flex; align-items:center; gap:4px; min-height:32px; margin:0; padding:4px 8px; font-size:var(--usx-font-size-sm); }
.connections input:not([type=checkbox]),.connections select { box-sizing:border-box; height:32px; min-height:32px; margin:0; padding:4px 8px; font:inherit; }.connections input[type=number]{width:6rem;}.connections input[type=checkbox]{margin:0;}
.connections textarea { width:100%; box-sizing:border-box; padding:8px; font:inherit; }.connections pre { white-space:pre-wrap; overflow-wrap:anywhere; max-height:20rem; overflow:auto; font-size:var(--usx-font-size-sm); }
.connection-actions { justify-content:flex-start; }.connection-preview { display:grid; gap:6px; max-height:16rem; overflow:auto; }.collection-row { justify-content:space-between; text-align:left; }.duplicate-row { display:flex; gap:8px; align-items:center; }

.merge-comparison {display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;}.merge-comparison article{display:grid;gap:8px;padding:8px;border:1px solid var(--usx-color-border);}.incoming-values{display:grid;grid-template-columns:auto 1fr;gap:6px;margin:0;}.incoming-values dd{margin:0;overflow-wrap:anywhere;}

/* Flat connection feed: no nested card shell or filled header. */
.connection-feed__entry { display: grid; gap: var(--usx-spacing-sm); min-width: 0; padding-block: var(--usx-spacing-md); border-bottom: 1px solid var(--usx-color-border); background: transparent; overflow-wrap: anywhere; }
.connection-feed__entry > header { background: transparent; border: 0; padding: 0; margin: 0; }
.connection-feed__entry > header h3 { font-size: var(--usx-font-size-base); }
.connection-feed__entry > header span, .connection-feed__entry > small { font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); }
.connection-feed__settings { margin: 0; padding: 0; border: 0; background: transparent; }
.connection-feed__settings > summary { cursor: pointer; padding-block: var(--usx-spacing-sm); font-size: var(--usx-font-size-sm); }
.connection-feed__settings[open] { display: grid; gap: var(--usx-spacing-sm); }
.connection-feed__settings .connection-scope { border: 0; border-left: 2px solid var(--usx-color-border); border-radius: 0; }
</style>

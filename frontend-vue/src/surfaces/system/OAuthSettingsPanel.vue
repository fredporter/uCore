<template>
  <section class="oauth-settings" aria-labelledby="oauth-heading">
    <h3 id="oauth-heading">Google OAuth</h3>
    <p>Configure this installation’s Desktop app once. Each person chooses their Google account in Connections.</p>
    <p role="status">{{ status.configured ? 'App credentials saved · ready for account sign-in' : 'App credentials needed' }}<span v-if="!status.encrypted_storage"> · encrypted storage unavailable</span></p>
    <form @submit.prevent="save">
      <label for="oauth-client-id">Client ID</label><input id="oauth-client-id" v-model="clientId" autocomplete="off" :placeholder="status.client_id_present ? 'Saved · enter the same client ID to update' : '…apps.googleusercontent.com'" required />
      <label for="oauth-client-secret">Client secret</label><input id="oauth-client-secret" v-model="clientSecret" type="password" autocomplete="new-password" :placeholder="status.client_secret_present ? 'Saved · leave blank to keep' : 'From the Desktop app credentials'" />
      <span>Local callback</span><code>{{ status.callback || 'Loading…' }}</code>
      <div class="oauth-actions"><button class="usx-btn usx-btn--primary" :disabled="busy || !status.encrypted_storage || !clientId.trim()"><UIcon name="save" />Save credentials</button><button type="button" class="usx-btn" :disabled="busy" @click="load"><UIcon name="refresh" />Check configuration</button><button type="button" class="usx-btn" @click="router.push('/system?tab=connections')">Open Connections<UIcon name="arrow_forward" /></button></div>
    </form>
    <p>Checks confirm local configuration only. Account sign-in verifies the credentials with Google. Saved values are never returned to this form.</p>
    <p v-if="message" role="status">{{ message }}</p><p v-if="error" role="alert">{{ error }}</p>
  </section>
</template>
<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import UIcon from '../../skills/atoms/UIcon.vue';
import { UCORE_BASE } from '../../api/base';
const router=useRouter();
const status=ref({configured:false,client_id_present:false,client_secret_present:false,encrypted_storage:true,callback:''});
const clientId=ref(''),clientSecret=ref(''),busy=ref(false),error=ref(''),message=ref('');
async function request(body?:object){const response=await fetch(`${UCORE_BASE}/api/connections/oauth-settings`,{method:body?'POST':'GET',...(body?{headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{})});if(!response.ok)throw Error((await response.text()).slice(0,240));return response.json();}
async function load(){busy.value=true;error.value='';try{status.value=await request();}catch(exc){error.value=exc instanceof Error?exc.message:'Could not check configuration';}finally{busy.value=false;}}
async function save(){busy.value=true;error.value='';message.value='';try{status.value=await request({client_id:clientId.value,client_secret:clientSecret.value});clientId.value='';message.value='Credentials saved. Choose an account in Connections.';}catch(exc){error.value=exc instanceof Error?exc.message:'Could not save credentials';}finally{clientSecret.value='';busy.value=false;}}
onMounted(load);
</script>
<style scoped>
.oauth-settings{margin-bottom:24px;padding-bottom:20px;border-bottom:1px solid var(--usx-color-border);text-align:left}.oauth-settings p{font-size:var(--usx-font-size-sm);color:var(--usx-color-on-surface-muted)}form{display:grid;grid-template-columns:10rem minmax(0,28rem);align-items:center;gap:12px}input{width:100%;box-sizing:border-box;height:32px;margin:0;padding:4px 8px;border:1px solid var(--usx-color-border);border-radius:var(--usx-radius-sm);background:var(--usx-color-surface);color:inherit;font:inherit;box-shadow:none;outline:0}input:focus-visible{border-color:transparent;outline:2px solid var(--usx-color-primary);outline-offset:-2px}code{overflow-wrap:anywhere}.oauth-actions{grid-column:1/-1;display:flex;flex-wrap:wrap;gap:8px}.usx-btn{display:inline-flex;align-items:center;gap:6px;margin:0}.oauth-settings [role=alert]{color:var(--usx-color-danger)}@media(max-width:40rem){form{grid-template-columns:1fr;gap:8px}}
</style>

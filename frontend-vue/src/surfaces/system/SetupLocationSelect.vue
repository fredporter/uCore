<template>
  <div class="location-select">
    <label :for="id">{{ label }}</label>
    <input :id="id" :value="modelValue" role="combobox" aria-autocomplete="list" :aria-expanded="open && filtered.length > 0" :aria-controls="id+'-options'" :aria-activedescendant="open && active>=0 ? id+'-option-'+active : undefined" :autocomplete="autocomplete" @input="input" @focus="open=true" @blur="open=false" @keydown="key" />
    <ul v-if="open && filtered.length" :id="id+'-options'" role="listbox" :aria-label="label+' suggestions'">
      <li v-for="(option,index) in filtered" :key="option" :id="id+'-option-'+index" role="option" :aria-selected="active===index" @mousedown.prevent @click="choose(option)">{{ option }}</li>
    </ul>
  </div>
</template>
<script setup lang="ts">
import { computed, ref, watch } from 'vue';
const props=defineProps<{id:string;label:string;modelValue:string;options:string[];autocomplete:string}>();
const emit=defineEmits<{ 'update:modelValue':[value:string];select:[value:string] }>();
const open=ref(false),active=ref(-1);
const filtered=computed(()=>props.options.filter(option=>option.toLocaleLowerCase().includes(props.modelValue.trim().toLocaleLowerCase())).slice(0,12));
watch(()=>props.modelValue,()=>{active.value=-1;});
function input(event:Event){emit('update:modelValue',(event.target as HTMLInputElement).value);open.value=true;}
function choose(value:string){emit('update:modelValue',value);emit('select',value);open.value=false;active.value=-1;}
function key(event:KeyboardEvent){if(event.key==='Escape'){open.value=false;return;}if(event.key==='ArrowDown'||event.key==='ArrowUp'){event.preventDefault();open.value=true;const n=filtered.value.length;if(n)active.value=(active.value+(event.key==='ArrowDown'?1:-1)+n)%n;}else if(event.key==='Enter'&&open.value&&active.value>=0){event.preventDefault();choose(filtered.value[active.value]);}}
</script>
<style scoped>
.location-select{position:relative;display:grid;gap:10px}.location-select label{margin:0}.location-select input{box-sizing:border-box;width:100%;height:44px;padding:8px 12px;margin:0;border:1px solid var(--usx-color-border);border-radius:var(--usx-radius-sm);background:var(--usx-color-surface);color:inherit;font:inherit;box-shadow:none;outline:0}.location-select input:focus-visible{outline:2px solid var(--usx-color-primary);outline-offset:-2px;border-color:transparent}ul{position:absolute;z-index:10;top:100%;left:0;right:0;max-height:14rem;overflow:auto;padding:4px;margin:4px 0 0;list-style:none;background:var(--usx-color-surface);border:1px solid var(--usx-color-border);border-radius:var(--usx-radius-sm);box-shadow:var(--usx-shadow-md)}li{padding:8px 12px;cursor:pointer;border-radius:var(--usx-radius-sm)}li:hover,li[aria-selected=true]{background:var(--usx-color-primary-soft,var(--usx-color-surface-hover));color:var(--usx-color-primary)}
</style>

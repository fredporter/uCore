// @vitest-environment jsdom
import { mount, flushPromises } from '@vue/test-utils';
import { createPinia } from 'pinia';
import { afterEach, expect, it, vi } from 'vitest';
import UserSetupSurface from './UserSetupSurface.vue';
vi.mock('vue-router',()=>({useRouter:()=>({push:vi.fn(),replace:vi.fn()})}));
vi.mock('../../stores/identity',()=>({useIdentityStore:()=>({load:vi.fn(),displayName:'Local user'})}));
vi.mock('../../stores/settings',()=>({useSettingsStore:()=>({themeMode:'dark',fontSize:16})}));
const perth={city:'Perth',country:'Australia',timezone:'Australia/Perth',point:{latitude:-31.95,longitude:115.85}};
const brisbane={city:'Brisbane',country:'Australia',timezone:'Australia/Brisbane',point:{latitude:-27.46,longitude:153.03}};
const catalog={source:'system-iana-tzdata',locations:[perth,brisbane],countries:['Australia'],suggestion:perth,readiness:{knowledge_library:true,gridcore_protocols:true,gridcore_mapping:true,maps:[{id:'world-map',name:'World Map',format:'ucode-layer-map-v1',projection:'equirectangular',cols:40,rows:25,bounds:{latMin:-60,latMax:85,lonMin:-180,lonMax:180}}]}};
function setup(responses:any,seeds:any=catalog){
 const fetchMock=vi.fn(async(url:string)=>({ok:true,json:async()=>url.includes('/setup/locations')?seeds:{setup:{step:1,completed:false},setup_story:responses?{responses}:null}}));
 vi.stubGlobal('fetch',fetchMock);
 const wrapper=mount(UserSetupSurface,{global:{plugins:[createPinia()],stubs:{ConnectionsPanel:true}}});
 return {wrapper,fetchMock};
}
afterEach(()=>{vi.unstubAllGlobals();});
it('resumes edited location without reseeding and saves the selected GridCore cell',async()=>{
 const {wrapper,fetchMock}=setup({display_name:'Alice',city:'Brisbane',country:'Australia',theme_mode:'light',font_size:'18',location_seeded:'true'});
 await flushPromises();
 expect((wrapper.get('#setup-city').element as HTMLInputElement).value).toBe('Brisbane');
 expect(fetchMock.mock.calls).toHaveLength(2);
 expect(wrapper.text()).toContain('Global Knowledge Library · Available');
 expect(wrapper.text()).toContain('GridCore · World Map');
 expect(wrapper.text()).not.toContain('optional');
 const next=wrapper.findAll('button').find(button=>button.text().includes('Next'))!;
 await next.trigger('click');await flushPromises();
 const options=(fetchMock.mock.calls[2] as any)[1];
 expect(JSON.parse(options.body)).toMatchObject({step:2,completed:false,answers:{city:'Brisbane',country:'Australia',location_seeded:'true',grid_location:{map:'world-map',column:37,row:19}}});
 wrapper.unmount();
});
it('seeds an untouched story once and persists the seed marker',async()=>{
 const {wrapper,fetchMock}=setup(null);await flushPromises();
 expect((wrapper.get('#setup-city').element as HTMLInputElement).value).toBe('Perth');
 const options=(fetchMock.mock.calls[2] as any)[1];
 expect(JSON.parse(options.body).answers).toMatchObject({city:'Perth',country:'Australia',location_seeded:'true'});
 wrapper.unmount();
});
it('preserves intentionally cleared fields on resume',async()=>{
 const {wrapper,fetchMock}=setup({city:'',country:'',location_seeded:'true'});await flushPromises();
 expect((wrapper.get('#setup-city').element as HTMLInputElement).value).toBe('');
 expect(fetchMock.mock.calls).toHaveLength(2);wrapper.unmount();
});
it('shows missing seed data and prevents advancing the location step',async()=>{
 const {wrapper}=setup({city:'Perth',country:'Australia',location_seeded:'true'},{...catalog,readiness:{...catalog.readiness,knowledge_library:false}});await flushPromises();
 expect(wrapper.text()).toContain('Global Knowledge Library · Needs installation');
 expect(wrapper.findAll('button').find(button=>button.text().includes('Next'))!.attributes('disabled')).toBeDefined();wrapper.unmount();
});

it('seeds an older untouched blank draft once',async()=>{
 const {wrapper,fetchMock}=setup({city:'',country:''});await flushPromises();
 expect((wrapper.get('#setup-city').element as HTMLInputElement).value).toBe('Perth');
 expect(fetchMock.mock.calls).toHaveLength(3);wrapper.unmount();
});

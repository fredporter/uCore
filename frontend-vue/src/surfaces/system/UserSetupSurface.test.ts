// @vitest-environment jsdom
import { mount, flushPromises } from '@vue/test-utils';
import { createPinia } from 'pinia';
import { expect, it, vi } from 'vitest';
import UserSetupSurface from './UserSetupSurface.vue';
vi.mock('vue-router',()=>({useRouter:()=>({push:vi.fn(),replace:vi.fn()})}));
vi.mock('../../stores/identity',()=>({useIdentityStore:()=>({load:vi.fn(),displayName:'Local user'})}));
vi.mock('../../stores/settings',()=>({useSettingsStore:()=>({themeMode:'dark',fontSize:16})}));
it('resumes a private setup draft without completing it or connecting accounts',async()=>{
  const fetchMock=vi.fn(async()=>({ok:true,json:async()=>({setup:{step:1,completed:false},setup_story:{responses:{display_name:'Alice',city:'Perth',theme_mode:'light',font_size:'18'}}})}));
  vi.stubGlobal('fetch',fetchMock);
  const wrapper=mount(UserSetupSurface,{global:{plugins:[createPinia()],stubs:{ConnectionsPanel:true}}});
  await flushPromises();
  expect(wrapper.text()).toContain('Where are you based?');
  expect((wrapper.get('input#setup-city').element as HTMLInputElement).value).toBe('Perth');
  expect(fetchMock.mock.calls).toHaveLength(1);
  await wrapper.get('input#setup-city').setValue('Fremantle');
  const next=wrapper.findAll('button').find(button=>button.text().includes('Next'))!;
  await next.trigger('click');await flushPromises();
  const options=(fetchMock.mock.calls[1] as any)[1];
  expect(JSON.parse(options.body)).toMatchObject({step:2,completed:false,answers:{city:'Fremantle',theme_mode:'light',font_size:'18'}});
  wrapper.unmount();
});

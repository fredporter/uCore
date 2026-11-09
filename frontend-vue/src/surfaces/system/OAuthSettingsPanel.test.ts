// @vitest-environment jsdom
import { mount, flushPromises } from '@vue/test-utils';
import { expect, it, vi } from 'vitest';
import OAuthSettingsPanel from './OAuthSettingsPanel.vue';
vi.mock('vue-router',()=>({useRouter:()=>({push:vi.fn()})}));
it('loads presence only and clears the secret after saving',async()=>{
  const fetchMock=vi.fn(async()=>({ok:true,json:async()=>({configured:true,client_id_present:true,client_secret_present:true,encrypted_storage:true,callback:'http://127.0.0.1:8484/api/connections/google/callback'})}));
  vi.stubGlobal('fetch',fetchMock);
  const wrapper=mount(OAuthSettingsPanel);await flushPromises();
  expect((wrapper.get('#oauth-client-id').element as HTMLInputElement).value).toBe('');
  expect((wrapper.get('#oauth-client-secret').element as HTMLInputElement).value).toBe('');
  await wrapper.get('#oauth-client-id').setValue('example.apps.googleusercontent.com');
  await wrapper.get('#oauth-client-secret').setValue('private-secret');
  await wrapper.get('form').trigger('submit');await flushPromises();
  expect(JSON.parse((fetchMock.mock.calls[1] as any)[1].body).client_secret).toBe('private-secret');
  expect((wrapper.get('#oauth-client-secret').element as HTMLInputElement).value).toBe('');
  expect(wrapper.text()).toContain('Credentials saved');wrapper.unmount();
});

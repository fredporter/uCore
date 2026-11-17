// @vitest-environment jsdom
import { mount, flushPromises } from '@vue/test-utils';
import { createPinia } from 'pinia';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import ConnectionsPanel from './ConnectionsPanel.vue';
const { route } = vi.hoisted(() => ({ route: { query: {} as Record<string, string> } }));
vi.mock('vue-router',()=>({useRouter:()=>({push:vi.fn()}),useRoute:()=>route}));

beforeEach(()=>{
  route.query = {};
  vi.stubGlobal('localStorage',{getItem:()=>null,setItem:vi.fn()});
});
describe('connection setup',()=>{
  it('does not import or enable sources just by opening setup',async()=>{
    const fetchMock=vi.fn(async(url:string)=>({ok:true,json:async()=>url.endsWith('/records')?{records:[]}:{setup:{completed:false},connections:[],counts:{},duplicates:[],conflicts:[]}}));
    vi.stubGlobal('fetch',fetchMock);
    const wrapper=mount(ConnectionsPanel,{global:{plugins:[createPinia()]}});
    await flushPromises();
    expect(wrapper.text()).toContain('Set up your workspace');
    expect(wrapper.text()).toContain('Add Google account');
    expect(fetchMock.mock.calls.every(call=>!call[0].includes('/sync')&&!call[0].includes('/discover'))).toBe(true);
    wrapper.unmount();
  });
  it('creates a disabled scoped connection and leaves account selection explicit',async()=>{
    const fetchMock=vi.fn(async(url:string,options?:any)=>({ok:true,json:async()=>url.endsWith('/records')?{records:[]}:options?.method==='POST'?{id:'created'}:{setup:{completed:true},connections:[],counts:{},duplicates:[],conflicts:[]}}));
    vi.stubGlobal('fetch',fetchMock);
    const wrapper=mount(ConnectionsPanel,{global:{plugins:[createPinia()]}});
    await flushPromises();
    const button=wrapper.findAll('button').find(button=>button.text().includes('Add Google account'))!;
    await button.trigger('click');await flushPromises();
    const post=fetchMock.mock.calls.find(call=>call[1]?.method==='POST')!;
    const body=JSON.parse(post[1].body);
    expect(body.provider).toBe('google');
    expect(body.config.enabled).toBe(false);
    expect(body.config.collections.tasks.lists).toEqual([]);
    expect(fetchMock.mock.calls.some(call=>call[0].includes('/authorize'))).toBe(false);
    wrapper.unmount();
  });
});

it('keeps same-name task lists separate within an account', async () => {
  route.query = { account: 'google-fixture' };
  const records = [
    { id: 'tasks:list-1/one', kind: 'tasks', data: { title: 'First task', list: 'Today', source_list_id: 'list-1' } },
    { id: 'tasks:list-2/two', kind: 'tasks', data: { title: 'Second task', list: 'Today', source_list_id: 'list-2' } },
  ];
  const fetchMock = vi.fn(async (url: string) => ({
    ok: true,
    json: async () => url.endsWith('/records?account=google-fixture')
      ? { records }
      : { setup: { completed: true }, connections: [], counts: {} },
  }));
  vi.stubGlobal('fetch', fetchMock);
  const wrapper = mount(ConnectionsPanel, {
    props: { collectionOnly: true, initialKind: 'tasks' },
    global: { plugins: [createPinia()] },
  });
  await flushPromises();
  const lists = wrapper.findAll('ul');
  expect(lists.map(list => list.text())).toEqual(['First task', 'Second task']);
  wrapper.unmount();
});

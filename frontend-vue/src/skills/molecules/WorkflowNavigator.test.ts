// @vitest-environment jsdom
import { mount, flushPromises } from '@vue/test-utils';
import { reactive } from 'vue';
import { beforeEach, expect, it, vi } from 'vitest';
const fixture = vi.hoisted(() => ({ store: {} as any }));
vi.mock('../../stores/workflow', () => ({ useWorkflowStore: () => fixture.store }));
import WorkflowNavigator from './WorkflowNavigator.vue';
beforeEach(() => {
  fixture.store = reactive({ activeBinderId: 'garden', activeList: '', selectedTask: null,
    binders: [{ id: 'garden', title: 'Garden' }], binderChoices: [{ id: 'garden', title: 'Garden', hasContent: true }],
    tasks: [{}], relatedTasks: [], scopedTasks: [], locationLabel: 'Garden',
    fetchTasks: vi.fn(), fetchBinders: vi.fn(async () => {}), showList: vi.fn(), showBinder: vi.fn(),
  });
});
async function start() {
  const wrapper = mount(WorkflowNavigator);
  await wrapper.findAll('button').find(button => button.text().includes('Rename Binder'))!.trigger('click');
  return wrapper;
}
it('saves a trimmed title against the original stable ID even when selection changes', async () => {
  const request = vi.fn(async () => new Response(JSON.stringify({ success: true })));
  vi.stubGlobal('fetch', request);
  fixture.store.fetchBinders = vi.fn(async () => { fixture.store.binders[0].title = 'Spring garden'; fixture.store.binderChoices[0].title = 'Spring garden'; });
  const wrapper = await start();
  await wrapper.get('#binder-name').setValue('  Spring garden  ');
  fixture.store.activeBinderId = 'other';
  await wrapper.get('form').trigger('submit'); await flushPromises();
  expect(request).toHaveBeenCalledWith(expect.stringContaining('/garden/title'), expect.objectContaining({method:'PATCH',body:JSON.stringify({title:'Spring garden'})}));
  expect(fixture.store.fetchBinders).toHaveBeenCalledWith(true);
  expect(wrapper.text()).toContain('Spring garden'); expect(wrapper.find('form').exists()).toBe(false);
  wrapper.unmount();
});
it('retains the edit and original title after a failed save', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify({error:'Rename unavailable'}), {status:503})));
  const wrapper = await start(); await wrapper.get('#binder-name').setValue('New name');
  await wrapper.get('form').trigger('submit'); await flushPromises();
  expect(wrapper.get('[role="alert"]').text()).toBe('Rename unavailable');
  expect(wrapper.find('form').exists()).toBe(true); expect(fixture.store.binders[0].title).toBe('Garden');
  wrapper.unmount();
});
it('does not send blank names and allows cancelling without writes', async () => {
  const request=vi.fn(); vi.stubGlobal('fetch', request);
  const wrapper=await start(); await wrapper.get('#binder-name').setValue(' ');
  await wrapper.get('form').trigger('submit'); expect(request).not.toHaveBeenCalled();
  await wrapper.findAll('button').find(button=>button.text()==='Cancel')!.trigger('click');
  expect(wrapper.find('form').exists()).toBe(false); expect(request).not.toHaveBeenCalled(); wrapper.unmount();
});

// @vitest-environment jsdom
import { afterEach, expect, it, vi } from 'vitest';
import { shallowMount, flushPromises } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import NotebookBinderPanel from './NotebookBinderPanel.vue';
import { useWorkflowStore } from '../../../stores/workflow';

afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals(); });
it('opens the selected binder draft in the shared Editor with its conflict hash', async () => {
  setActivePinia(createPinia());
  const store = useWorkflowStore();
  store.binders = [{ id: 'project', title: 'Project' }];
  store.activeBinderId = 'project';
  vi.spyOn(store, 'fetchBinders').mockResolvedValue();
  vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify({ binder: {
    metadata: { title: 'Project', state: 'draft_brief' }, brief: '# Brief', draft: '# Draft', draft_sha256: 'base-hash',
    requirements: [], sources: [], plan: [], evidence: [], decisions: [], editions: [],
  }, dispatches: [], items: [], catalog: [] }))));
  const wrapper = shallowMount(NotebookBinderPanel);
  await flushPromises();
  const open = wrapper.findAll('button').find(button => button.text() === 'Open draft in Editor');
  expect(open).toBeDefined();
  await open!.trigger('click');
  expect(store.activeTab).toBe('editor');
  expect(store.binderDocument?.binderId).toBe('project');
  expect(store.binderDocument?.baseHash).toBe('base-hash');
  expect(store.selectedFile?.content).toBe('# Draft');
  store.binderCreateRequested = true;
  await flushPromises();
  expect(wrapper.find('.modal-backdrop').exists()).toBe(true);
  expect(store.binderCreateRequested).toBe(false);
  wrapper.unmount();
});

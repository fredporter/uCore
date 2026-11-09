// @vitest-environment jsdom
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { mount, shallowMount, flushPromises } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import NotebookBinderPanel from './NotebookBinderPanel.vue';
import { useWorkflowStore } from '../../../stores/workflow';
vi.mock('../../../utils/diagramHydrator', () => ({ hydrateDiagrams: vi.fn() }));
const document = { filename: 'seeds.md', path: '/Binders/garden/docs/seeds.md' };
const content = '---\ntitle: Garden\ntags: [planting]\n---\n# Garden\n## Plan\n<img src="x" onerror="alert(1)">\n\n[Seeds](docs/seeds.md)';
beforeEach(() => {
  setActivePinia(createPinia());
  const wf = useWorkflowStore();
  wf.binders = [{ id: 'garden', title: 'Garden' }];
  wf.showBinder('garden');
  vi.spyOn(wf, 'fetchBinders').mockResolvedValue();
  vi.stubGlobal('fetch', vi.fn(async (url: string) => new Response(JSON.stringify(url.includes('/dispatch/') ? { dispatches: [] } : { binder: { metadata: { id: 'garden', title: 'Garden', state: 'draft_brief' }, brief: content, draft: content, documents: [document], sources: [], requirements: [], decisions: [], evidence: [], editions: [] } }))));
});
afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals(); });

it('shares safe properties, contents and prose between Binder brief and draft', async () => {
  const wrapper = mount(NotebookBinderPanel);
  await flushPromises();
  expect(wrapper.find('.reading-article').exists()).toBe(true);
  expect(wrapper.find('[aria-label="Document properties"]').text()).toContain('planting');
  expect(wrapper.find('[aria-label="Document contents"]').text()).toContain('Plan');
  expect(wrapper.find('img[onerror]').exists()).toBe(false);
  useWorkflowStore().binderStage = 'draft';
  await flushPromises();
  expect(wrapper.find('.reading-article').exists()).toBe(true);
  expect(wrapper.find('img[onerror]').exists()).toBe(false);
  wrapper.unmount();
});

it('opens attached documents through the shared Editor and rejects unrelated links', async () => {
  const open = vi.spyOn(useWorkflowStore(), 'openVaultDocument').mockResolvedValue();
  const wrapper = mount(NotebookBinderPanel);
  await flushPromises();
  await wrapper.get('a[href="docs/seeds.md"]').trigger('click');
  await flushPromises();
  expect(open).toHaveBeenCalledWith(document.path, document.filename, 'garden');
  open.mockClear();
  await (wrapper.vm as any).openBinderLink('../../other/private.md');
  expect(open).not.toHaveBeenCalled();
  expect(wrapper.text()).toContain('not attached to the selected Binder');
  wrapper.unmount();
});

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

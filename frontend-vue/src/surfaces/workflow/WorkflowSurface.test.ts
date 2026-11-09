// @vitest-environment jsdom
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { shallowMount, flushPromises } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { defineComponent } from 'vue';
import WorkflowSurface from './WorkflowSurface.vue';
import { useWorkflowStore } from '../../stores/workflow';
import { useWorkspaceStore } from '../../stores/workspace';
import { getEditorSurface } from '../../composables/useEditorSurface';

vi.mock('vue-router', () => ({
  useRoute: () => ({ query: { tab: 'editor' } }),
  useRouter: () => ({ replace: vi.fn(), push: vi.fn() }),
}));
vi.mock('../../skills', () => ({
  EditorPanel: defineComponent({ name: 'EditorPanel', emits: ['save'], template: '<div />' }),
}));
vi.mock('@/api/preflight', () => ({
  ensureCapabilityReady: vi.fn(async (capability: string) => ({ capability, ready: true, repair: [] })),
}));

beforeEach(() => {
  const storage = new Map<string, string>();
  vi.stubGlobal('localStorage', { getItem: (key: string) => storage.get(key) ?? null, setItem: (key: string, value: string) => storage.set(key, value), removeItem: (key: string) => storage.delete(key) });
  setActivePinia(createPinia());
  getEditorSurface().closeEditor();
  vi.spyOn(useWorkspaceStore(), 'loadTree').mockResolvedValue();
  const wf = useWorkflowStore();
  vi.spyOn(wf, 'fetchAll').mockResolvedValue();
  wf.selectTask({ id: 'task-1', title: 'Task', status: 'todo', priority: 'medium', board: 'inbox', tags: [], description: 'Old body' });
  wf.setTab('editor');
});
afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals(); });

it('persists an editor Save and reports success after the response', async () => {
  const request = vi.fn(async (_url: RequestInfo | URL, _init?: RequestInit) => new Response(JSON.stringify({ updated: { id: 'task-1', title: 'Task', body: 'New body' } })));
  vi.stubGlobal('fetch', request);
  const wrapper = shallowMount(WorkflowSurface);
  wrapper.findComponent({ name: 'EditorPanel' }).vm.$emit('save', 'New body');
  await flushPromises();
  expect(request).toHaveBeenCalledWith(expect.stringContaining('/api/workflow/tasks/task-1'), expect.objectContaining({ method: 'PATCH', body: JSON.stringify({ body: 'New body' }) }));
  expect(wrapper.text()).toContain('Saved');
  expect(useWorkflowStore().selectedTask?.description).toBe('New body');
  wrapper.unmount();
});

it('shows a failed save without claiming success', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => new Response('', { status: 500 })));
  const wrapper = shallowMount(WorkflowSurface);
  wrapper.findComponent({ name: 'EditorPanel' }).vm.$emit('save', 'New body');
  await flushPromises();
  expect(wrapper.find('[role="alert"]').text()).toContain('HTTP 500');
  expect(wrapper.text()).not.toContain('Saved');
  wrapper.unmount();
});

it('keeps the selected task when navigating from Tasks into the shared Editor', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => new Response('{}')));
  const store = useWorkflowStore();
  const wrapper = shallowMount(WorkflowSurface);
  await flushPromises();
  store.setTab('tasks');
  await flushPromises();
  const task = { id: 'next-task', title: 'Next task', board: 'week', binder: '', status: 'todo', priority: 'medium' as const, tags: [], description: 'Task content' };
  store.openTask(task);
  await flushPromises();
  expect(store.selectedTask?.id).toBe('next-task');
  expect(store.activeTab).toBe('editor');
  expect(wrapper.findComponent({ name: 'EditorPanel' }).attributes('title')).toBe('Next task');
  wrapper.unmount();
});

it('navigates between related tasks without clearing Editor state', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => new Response('{}')));
  const store = useWorkflowStore();
  const first = store.selectedTask!;
  const next = { ...first, id: 'sibling', title: 'Z sibling task' };
  store.tasks = [first, next];
  store.openTask(first);
  const wrapper = shallowMount(WorkflowSurface);
  await flushPromises();
  await wrapper.find('button[aria-label="Next task"]').trigger('click');
  await flushPromises();
  expect(store.selectedTask?.id).toBe('sibling');
  expect(store.activeTab).toBe('editor');
  wrapper.unmount();
});

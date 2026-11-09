// @vitest-environment jsdom
import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import { useWorkflowStore } from './workflow';

vi.mock('@/api/preflight', () => ({
  ensureCapabilityReady: vi.fn(async (capability: string) => ({ capability, ready: true, repair: [] })),
}));

beforeEach(() => { setActivePinia(createPinia()); });
afterEach(() => { vi.unstubAllGlobals(); });

describe('workflow durable actions', () => {
  it('shows an empty task response without fabricated sample records', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify({ tasks: [] }))));
    const store = useWorkflowStore();
    expect(store.tasks).toEqual([]);
    await store.fetchTasks();
    expect(store.tasks).toEqual([]);
  });

  it('patches task content before reporting updated state', async () => {
    const request = vi.fn(async (_url: RequestInfo | URL, _init?: RequestInit) => new Response(JSON.stringify({ updated: { id: 'saved-task', title: 'Saved task', body: 'New content' } })));
    vi.stubGlobal('fetch', request);
    const store = useWorkflowStore();
    const updated = await store.patchTask('saved-task', { body: 'New content' });
    expect(request.mock.calls[0]?.[1]).toMatchObject({ method: 'PATCH', body: JSON.stringify({ body: 'New content' }) });
    expect(updated.description).toBe('New content');
  });

  it('does not report success when the task write fails', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response('', { status: 500 })));
    await expect(useWorkflowStore().patchTask('task', { body: 'Draft' })).rejects.toThrow('HTTP 500');
  });
});

describe('shared workflow context', () => {
  it('opens a task instead of the previously opened file and retains unsaved text between siblings', () => {
    const store = useWorkflowStore();
    const first = { id: 'one', title: 'One', board: 'week', binder: 'project', group: 'Next', status: 'todo', priority: 'medium' as const, tags: [], description: 'Original' };
    const second = { ...first, id: 'two', title: 'Two' };
    store.tasks = [first, second];
    store.selectFile({ id: 'file', path: '/notes.md', filename: 'notes.md', extension: 'md', binder: '', content: 'File contents', readOnly: false });
    store.openTask(first);
    expect(store.selectedFile).toBeNull();
    expect(store.editorKey).toBe('task:one');
    store.updateEditorContent('Unsaved draft');
    store.openTask(second);
    store.openTask(first);
    expect(store.editorDrafts[store.editorKey]).toBe('Unsaved draft');
    expect(first.description).toBe('Original');
    expect(store.locationLabel).toBe('project / Next');
    expect(store.orderedContextTasks).toHaveLength(2);
  });

  it('keeps binder draft conflict hashes when reopening unsaved content', async () => {
    const request = vi.fn(async (_url: RequestInfo | URL, _init?: RequestInit) => new Response(JSON.stringify({ draft_sha256: 'saved' })));
    vi.stubGlobal('fetch', request);
    const store = useWorkflowStore();
    store.openBinderDocument('project', 'Project draft', 'Original', 'original-hash');
    store.updateEditorContent('Unsaved');
    store.showList();
    store.openBinderDocument('project', 'Project draft', 'Concurrent change', 'different-hash');
    await store.saveBinderDocument('Unsaved');
    expect(request.mock.calls[0]?.[1]?.body).toBe(JSON.stringify({ content: 'Unsaved', expected_base_hash: 'original-hash' }));
    expect(store.hasEditorDraft).toBe(false);
  });

  it('moves or copies the actual dragged task through persistence', async () => {
    const store = useWorkflowStore();
    // Store closures call the underlying action, so verify transport rather than spies.
    vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify({ updated: { id: 'one', title: 'One', board: 'week', group: 'Next', status: 'todo' }, tasks: [] }))));
    const event = { dataTransfer: { getData: () => 'one' }, altKey: false, ctrlKey: false } as unknown as DragEvent;
    await store.dropTask(event, { board: 'week', group: 'Next' });
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/api/workflow/tasks/one'), expect.objectContaining({ method: 'PATCH', body: JSON.stringify({ board: 'week', group: 'Next' }) }));
    await store.dropTask({ ...event, altKey: true } as DragEvent, { board: 'later' });
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/api/workflow/tasks/one/duplicate'), expect.objectContaining({ method: 'POST', body: JSON.stringify({ board: 'later' }) }));
  });
});

it('shares concurrent Binder loads across surfaces and refreshes after a change', async () => {
  let finish!: (response: Response) => void;
  const pending = new Promise<Response>(resolve => { finish = resolve; });
  const request = vi.fn().mockReturnValueOnce(pending).mockResolvedValue(new Response(JSON.stringify({binders:[{id:'updated',title:'Updated'}]})));
  vi.stubGlobal('fetch', request);
  const store = useWorkflowStore();
  const first = store.fetchBinders(), second = store.fetchBinders();
  expect(request).toHaveBeenCalledTimes(1);
  finish(new Response(JSON.stringify({binders:[{id:'original',title:'Original'}]})));
  await Promise.all([first,second]);
  expect(store.binders[0].id).toBe('original');
  await store.fetchBinders(true);
  expect(request).toHaveBeenCalledTimes(2);
  expect(store.binders[0].id).toBe('updated');
});


it('loads an empty Workflow without calling the retired mission projection', async () => {
  const request = vi.fn(async (_url: RequestInfo | URL) => new Response(JSON.stringify({binders:[],tasks:[],workflows:[],runs:[],tasker:{boards:[]}})));
  vi.stubGlobal('fetch',request);
  const store=useWorkflowStore();
  await store.fetchAll();
  expect(request.mock.calls.every(call=>!String(call[0]).includes('mission-task-binder'))).toBe(true);
  expect(store.error).toBe(null);
  expect(store.tasks).toEqual([]);
});

it('opens a saved Binder document through the shared reader with its persisted version', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify({ content: '---\nbinder: garden\n---\n\nSaved note', version: 'disk-version' }))));
  const store = useWorkflowStore();
  store.binders = [{ id: 'garden', title: 'Garden' }];
  await store.openVaultDocument('/Binders/garden/docs/seeds.md', 'seeds.md', 'garden');
  expect(store.activeBinderId).toBe('garden');
  expect(store.selectedFile).toMatchObject({ content: expect.stringContaining('Saved note'), version: 'disk-version', binder: 'garden' });
  expect(store.activeTab).toBe('editor');
});

it('does not replace the current Workflow item when a document cannot be read', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => new Response('', { status: 404 })));
  const store = useWorkflowStore();
  store.binders = [{ id: 'garden' }];
  store.showBinder('garden');
  await expect(store.openVaultDocument('/Binders/garden/docs/missing.md', 'missing.md', 'garden')).rejects.toThrow();
  expect(store.activeTab).toBe('mission-control');
  expect(store.activeBinderId).toBe('garden');
});

it('shows Binder siblings across source boards and resolves known legacy list links', () => {
  const store = useWorkflowStore();
  store.binders = [{ id: 'garden', title: 'Garden' }];
  const task = { id: 'one', title: 'One', board: 'apple-family', binder: 'garden', group: '', status: 'todo', priority: 'medium' as const, tags: [], description: '' };
  store.tasks = [task, { ...task, id: 'two', board: 'google-personal' }, { ...task, id: 'other', binder: 'another' }];
  store.openTask(task);
  expect(store.activeList).toBe('');
  expect(store.relatedTasks.map(task => task.id)).toEqual(['one', 'two']);
  store.showList('garden');
  expect(store.activeBinderId).toBe('garden');
  expect(store.activeList).toBe('');
  expect(store.scopedTasks).toHaveLength(2);
  store.showList('apple-family');
  expect(store.activeBinderId).toBe('');
  expect(store.scopedTasks.map(task => task.id)).toEqual(['one', 'other']);
});

it('moves Binder membership without rewriting the source board', async () => {
  const request = vi.fn(async () => new Response(JSON.stringify({ updated: { id: 'one', title: 'One', board: 'apple-family', binder: 'garden', status: 'todo' } })));
  vi.stubGlobal('fetch', request);
  const store = useWorkflowStore();
  await store.dropTask({ dataTransfer: { getData: () => 'one' }, altKey: false, ctrlKey: false } as unknown as DragEvent, { binder: 'garden' });
  expect(request).toHaveBeenCalledWith(expect.stringContaining('/tasks/one'), expect.objectContaining({ body: JSON.stringify({ binder: 'garden' }) }));
});

// @vitest-environment jsdom
import { afterEach, expect, it, vi } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import { useWorkspaceStore } from './workspace';
import { getEditorSurface } from '../composables/useEditorSurface';

afterEach(() => { vi.unstubAllGlobals(); getEditorSurface().closeEditor(); });
it('advances the open file version after each successful save', async () => {
  setActivePinia(createPinia());
  getEditorSurface().openFile({ path: '/Note.md', filename: 'Note.md', content: 'Original', extension: 'md', version: 'v1' });
  let revision = 1;
  const request = vi.fn(async (_url: RequestInfo | URL, _init?: RequestInit) => new Response(JSON.stringify({ version: `v${++revision}` })));
  vi.stubGlobal('fetch', request);
  const store = useWorkspaceStore();
  await store.saveFile('/Note.md', 'First edit', getEditorSurface().currentFile.value?.version);
  expect(getEditorSurface().currentFile.value?.version).toBe('v2');
  await store.saveFile('/Note.md', 'Second edit', getEditorSurface().currentFile.value?.version);
  expect(JSON.parse(String(request.mock.calls[1]?.[1]?.body)).version).toBe('v2');
  expect(getEditorSurface().currentFile.value?.version).toBe('v3');
});

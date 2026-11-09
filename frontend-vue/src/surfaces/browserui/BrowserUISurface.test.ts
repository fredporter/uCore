// @vitest-environment jsdom
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { shallowMount, flushPromises } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import BrowserUISurface from './BrowserUISurface.vue';
import { startResearch, listResearchJobs, addBinder } from './ApiBridge';
import { useWorkflowStore } from '../../stores/workflow';
import { ucoreApi } from '../../api/client';

vi.mock('vue-router', () => ({
  useRoute: () => ({ query: {} }),
  useRouter: () => ({ replace: vi.fn(), push: vi.fn() }),
}));
vi.mock('./ApiBridge', () => ({
  startResearch: vi.fn(async () => ({ job_id: 'job-1' })),
  listResearchJobs: vi.fn(async () => []),
  addBinder: vi.fn(), fetchScrape: vi.fn(), searchResearch: vi.fn(),
  searchGrounded: vi.fn(), getActiveSafariTab: vi.fn(), exportToAppleNotes: vi.fn(),
}));
vi.mock('../../stores/chat', () => ({ useChatStore: () => ({ sendMessage: vi.fn() }) }));

beforeEach(() => {
  setActivePinia(createPinia());
  localStorage.clear();
  vi.clearAllMocks();
  vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify({ documents: [], items: [], gaps: [] }))));
});
afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals(); });

it('loads only the selected Binder jobs and keeps new jobs in that context', async () => {
  const wrapper = shallowMount(BrowserUISurface, { props: { embedded: true, queueOnly: true, binderId: 'garden' } });
  await flushPromises();
  expect(listResearchJobs).toHaveBeenCalledWith(undefined, 'garden');
  wrapper.findComponent({ name: 'ResearchDashboard' }).vm.$emit('startResearch', { url: 'https://example.com', binder: 'other' });
  await flushPromises();
  expect(startResearch).toHaveBeenCalledWith('https://example.com', 'garden', [], 'full');
  wrapper.unmount();
});

it('keeps the cross-workspace Queue unfiltered', async () => {
  const wrapper = shallowMount(BrowserUISurface, { props: { embedded: true, queueOnly: true } });
  await flushPromises();
  expect(listResearchJobs).toHaveBeenCalledWith(undefined, undefined);
  wrapper.unmount();
});

it('saves into the selected Binder without creating another Binder', async () => {
  vi.spyOn(useWorkflowStore(), 'openVaultDocument').mockResolvedValue();
  const imported = vi.spyOn(ucoreApi.userWorkflow, 'importMarkdown').mockResolvedValue({ ok: true, status: 200, data: { path: '/notes/research.md' } });
  const wrapper = shallowMount(BrowserUISurface, { props: { embedded: true, binderId: 'garden' } });
  await flushPromises();
  await (wrapper.vm as any).saveToBinder({ title: 'Seeds', content: 'Plant in spring', tags: ['#garden'] });
  expect(imported).toHaveBeenCalledWith(expect.objectContaining({ binder: 'garden', require_existing_binder: true, content: 'Plant in spring' }));
  expect(addBinder).not.toHaveBeenCalled();
  wrapper.unmount();
});

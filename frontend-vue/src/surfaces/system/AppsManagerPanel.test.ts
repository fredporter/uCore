// @vitest-environment jsdom
import { mount, flushPromises } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { reactive } from 'vue';
import { beforeEach, expect, it, vi } from 'vitest';
import { useShellStore } from '../../stores/shell';
const routing = vi.hoisted(() => ({ route: {} as any, replace: vi.fn() }));
vi.mock('vue-router', () => ({ useRoute: () => routing.route, useRouter: () => ({ replace: routing.replace }) }));
import AppsManagerPanel from './AppsManagerPanel.vue';
beforeEach(() => {
  localStorage.clear(); setActivePinia(createPinia()); vi.clearAllMocks();
  routing.route = reactive({ query: { tab: 'apps', workspace: 'apple', collection: 'contacts', record: 'record-7' } });
  vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify({ platform: 'macos', apps: [], records: [] }))));
});
function render() { return mount(AppsManagerPanel, { global: { stubs: { ConnectionsPanel: { props: ['initialKind'], template: '<div data-test="records">{{ initialKind }}</div>' }, UIcon: true } } }); }
it('maps Vault selection to the existing browser and preserves record context', async () => {
  const shell = useShellStore(); shell.setSidebarMode('workflow');
  const wrapper = render(); await flushPromises();
  await wrapper.findAll('nav[aria-label="Workspaces"] button').find(button => button.text() === 'Vault')!.trigger('click');
  expect(shell.sidebarMode).toBe('vault'); expect(shell.sidebarOpen).toBe(true);
  expect(routing.replace).toHaveBeenCalledWith({ query: { tab: 'apps', workspace: 'vault', collection: 'contacts', record: 'record-7' } });
  wrapper.unmount();
});
it('normalizes a legacy local link without dropping the selected collection or record', async () => {
  routing.route.query.workspace = 'local';
  const wrapper = render(); await flushPromises();
  expect(routing.replace).toHaveBeenCalledWith({ query: { tab: 'apps', workspace: 'vault', collection: 'contacts', record: 'record-7' } });
  expect(wrapper.find('[data-test="records"]').text()).toBe('contacts');
  expect(useShellStore().sidebarOpen).toBe(true); wrapper.unmount();
});
it('keeps provider workspaces from opening the Vault browser', async () => {
  const wrapper = render(); await flushPromises();
  expect(useShellStore().sidebarOpen).toBe(false);
  expect(wrapper.text()).toContain('Apple Workspace'); wrapper.unmount();
});

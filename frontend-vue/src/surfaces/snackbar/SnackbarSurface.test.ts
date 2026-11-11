// @vitest-environment jsdom
import { shallowMount, flushPromises } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { createRouter, createMemoryHistory } from 'vue-router';
import { beforeEach, expect, it } from 'vitest';
import SnackbarSurface from './SnackbarSurface.vue';
beforeEach(() => { localStorage.clear(); setActivePinia(createPinia()); });
it.each(['tasks', 'contacts', 'notes'])('redirects legacy %s links to Vault with record/account context', async kind => {
  const router = createRouter({ history: createMemoryHistory(), routes: [
    { path: '/snackbar', component: SnackbarSurface }, { path: '/system', component: { template: '<div />' } },
  ] });
  await router.push({ path: '/snackbar', query: { tab: kind, record: 'record-7', account: 'account-2' } });
  await router.isReady();
  const wrapper = shallowMount(SnackbarSurface, { global: { plugins: [router] } });
  await flushPromises();
  expect(router.currentRoute.value.path).toBe('/system');
  expect(router.currentRoute.value.query).toEqual({ tab: 'apps', workspace: 'vault', collection: kind, record: 'record-7', account: 'account-2' });
  wrapper.unmount();
});

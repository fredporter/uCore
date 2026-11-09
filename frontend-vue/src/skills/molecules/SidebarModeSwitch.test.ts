// @vitest-environment jsdom
import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { beforeEach, expect, it } from 'vitest';
import SidebarModeSwitch from './SidebarModeSwitch.vue';
import { useShellStore } from '../../stores/shell';
beforeEach(() => { localStorage.clear(); setActivePinia(createPinia()); });
it('switches the shared sidebar mode and remembers the choice', async () => {
  const wrapper = mount(SidebarModeSwitch);
  const buttons = wrapper.findAll('button');
  expect(buttons[0].attributes('aria-pressed')).toBe('true');
  await buttons[1].trigger('click');
  expect(useShellStore().sidebarMode).toBe('workflow');
  expect(buttons[1].attributes('aria-pressed')).toBe('true');
  expect(localStorage.getItem('ucore-sidebar-mode')).toBe('workflow');
  wrapper.unmount();
  setActivePinia(createPinia());
  expect(useShellStore().sidebarMode).toBe('workflow');
});

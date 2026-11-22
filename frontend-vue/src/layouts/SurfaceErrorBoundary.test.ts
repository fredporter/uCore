// @vitest-environment jsdom
import { mount } from '@vue/test-utils';
import { defineComponent, h } from 'vue';
import { createMemoryHistory, createRouter } from 'vue-router';
import { expect, it, vi } from 'vitest';
import SurfaceErrorBoundary from './SurfaceErrorBoundary.vue';

it('shows a safe recovery page and remounts the surface on retry', async () => {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: '/', name: 'dashboard', component: { template: '<div />' } }],
  });
  await router.push('/');
  let canRender = false;
  const Surface = defineComponent({
    render() {
      if (!canRender) throw new Error('internal diagnostic');
      return h('p', 'Surface ready');
    },
  });
  const log = vi.spyOn(console, 'error').mockImplementation(() => {});
  try {
    const wrapper = mount(SurfaceErrorBoundary, {
      global: { plugins: [router] },
      slots: { default: Surface },
    });
    await wrapper.vm.$nextTick();
    expect(wrapper.get('h1').text()).toBe('This page couldn’t load');
    expect(wrapper.text()).not.toContain('internal diagnostic');
    canRender = true;
    await wrapper.get('button').trigger('click');
    expect(wrapper.text()).toContain('Surface ready');
    wrapper.unmount();
  } finally {
    log.mockRestore();
  }
});

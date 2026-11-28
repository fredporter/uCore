// @vitest-environment jsdom
import { mount } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';
import SurfaceTabNav from './SurfaceTabNav.vue';

const TABS = [
  { id: 'tools', label: 'Tools', icon: 'terminal' },
  { id: 'prose', label: 'Prose Recipes', icon: 'article' },
  { id: 'grid', label: 'Grid Recipes', icon: 'grid_on' },
];

function mountNav(modelValue = 'tools') {
  return mount(SurfaceTabNav, {
    props: { tabs: TABS, modelValue },
    slots: { actions: '<button class="pinned-action">Pin</button>' },
    // Detached mounts never receive focus, so the keyboard cases need a live element.
    attachTo: document.body,
  });
}

describe('SurfaceTabNav', () => {
  it('marks only the selected tab as the current page', () => {
    const wrapper = mountNav('prose');
    const links = wrapper.findAll('.surface-tab-nav__link');

    expect(links).toHaveLength(3);
    expect(links[0].attributes('aria-current')).toBeUndefined();
    expect(links[1].attributes('aria-current')).toBe('page');
    expect(links[2].attributes('aria-current')).toBeUndefined();
    expect(links[1].classes()).toContain('surface-tab-nav__link--active');
    wrapper.unmount();
  });

  it('emits the selected tab id on click', async () => {
    const wrapper = mountNav();
    await wrapper.findAll('.surface-tab-nav__link')[2].trigger('click');

    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual(['grid']);
    wrapper.unmount();
  });

  it('keeps every tab in the tab order', () => {
    const wrapper = mountNav('grid');
    const links = wrapper.findAll('.surface-tab-nav__link');

    for (const link of links) {
      expect(link.attributes('tabindex')).toBeUndefined();
      expect(link.attributes('href')).toBe('#');
    }
    wrapper.unmount();
  });

  it('moves focus with arrows, Home and End in a horizontal strip', async () => {
    const wrapper = mountNav('tools');
    const links = wrapper.findAll('.surface-tab-nav__link');
    const active = () => wrapper.element.ownerDocument.activeElement;

    (links[0].element as HTMLElement).focus();
    expect(active()).toBe(links[0].element);

    await links[0].trigger('keydown', { key: 'ArrowRight' });
    expect(active()).toBe(links[1].element);

    await links[1].trigger('keydown', { key: 'End' });
    expect(active()).toBe(links[2].element);

    await links[2].trigger('keydown', { key: 'ArrowRight' });
    expect(active()).toBe(links[0].element);

    await links[2].trigger('keydown', { key: 'Home' });
    expect(active()).toBe(links[0].element);
    wrapper.unmount();
  });

  it('uses arrow-up and arrow-down in a vertical strip', async () => {
    const wrapper = mount(SurfaceTabNav, {
      props: { tabs: TABS, modelValue: 'tools', orientation: 'vertical' },
      attachTo: document.body,
    });
    const links = wrapper.findAll('.surface-tab-nav__link');

    (links[0].element as HTMLElement).focus();
    await links[0].trigger('keydown', { key: 'ArrowDown' });
    expect(wrapper.element.ownerDocument.activeElement).toBe(links[1].element);

    await links[1].trigger('keydown', { key: 'ArrowUp' });
    expect(wrapper.element.ownerDocument.activeElement).toBe(links[0].element);
    wrapper.unmount();
  });

  it('keeps the actions slot outside the scrolling strip', () => {
    const wrapper = mountNav();
    const scroller = wrapper.find('.surface-tab-nav__scroll');

    expect(scroller.find('.surface-tab-nav__link').exists()).toBe(true);
    expect(scroller.find('.pinned-action').exists()).toBe(false);
    expect(wrapper.find('.surface-tab-nav__actions .pinned-action').exists()).toBe(true);
    wrapper.unmount();
  });

  it('survives a layout-free environment without scrolling the page', async () => {
    const wrapper = mountNav('grid');
    await wrapper.setProps({ modelValue: 'prose' });
    await wrapper.vm.$nextTick();

    expect(wrapper.find('.surface-tab-nav__scroll').element.scrollLeft).toBe(0);
    expect(wrapper.attributes('data-overflow-end')).toBeUndefined();
    wrapper.unmount();
  });
});

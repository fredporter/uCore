// @vitest-environment jsdom
import { expect, it } from 'vitest';
import { shallowMount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import WorkflowDashboardPanel from './WorkflowDashboardPanel.vue';
import { useWorkflowStore } from '../../../stores/workflow';

it('requires a Binder and replaces the research view when the selected Binder changes', async () => {
  setActivePinia(createPinia());
  const wf = useWorkflowStore();
  const wrapper = shallowMount(WorkflowDashboardPanel);
  const researchButton = wrapper.findAll('button.workflow-dashboard__card').at(1)!;
  await researchButton.trigger('click');
  expect(wrapper.text()).toContain('Select or create a Binder');
  expect(wrapper.findComponent({ name: 'BrowserUISurface' }).exists()).toBe(false);
  wf.showBinder('garden');
  await wrapper.vm.$nextTick();
  const first = wrapper.findComponent({ name: 'BrowserUISurface' });
  expect(first.props('binderId')).toBe('garden');
  wf.showBinder('reading');
  await wrapper.vm.$nextTick();
  const second = wrapper.findComponent({ name: 'BrowserUISurface' });
  expect(second.props('binderId')).toBe('reading');
  expect(second.vm === first.vm).toBe(false);
  wrapper.unmount();
});

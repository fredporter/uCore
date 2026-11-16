// @vitest-environment jsdom
import { expect, it } from 'vitest';
import { shallowMount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import WorkflowDashboardPanel from './WorkflowDashboardPanel.vue';
import { useWorkflowStore } from '../../../stores/workflow';

it('opens the dedicated resource tabs without clearing the selected Binder', async () => {
  setActivePinia(createPinia());
  const wf = useWorkflowStore();
  wf.activeBinderId = 'garden';
  const wrapper = shallowMount(WorkflowDashboardPanel);
  const [binders, research] = wrapper.findAll('button.workflow-dashboard__card');
  await binders.trigger('click');
  expect(wf.activeTab).toBe('binder');
  await research.trigger('click');
  expect(wf.activeTab).toBe('research');
  expect(wf.activeBinderId).toBe('garden');
  wrapper.unmount();
});

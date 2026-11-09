// @vitest-environment jsdom
import { afterEach, expect, it, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import MissionControlPanel from './MissionControlPanel.vue';
import { useWorkflowStore } from '../../../stores/workflow';
afterEach(() => vi.restoreAllMocks());
it('records an objective and uses mission context for Queue without inventing tasks', async () => {
  setActivePinia(createPinia());
  const wf = useWorkflowStore();
  const create = vi.spyOn(wf, 'createMission').mockImplementation(async title => {
    wf.missions = [{ id: 'mission-1', title, status: 'active', priority: 'medium', description: title, taskIds: [] }];
    wf.selectMission('mission-1');
  });
  const wrapper = mount(MissionControlPanel);
  expect(wrapper.text()).toContain('What would you like to do today?');
  await wrapper.get('input').setValue('Plan a garden');
  await wrapper.get('form').trigger('submit');
  await flushPromises();
  expect(create).toHaveBeenCalledWith('Plan a garden');
  expect(wf.tasks).toEqual([]);
  const queue = wrapper.findAll('button').find(button => button.text().includes('Queue'))!;
  await queue.trigger('click');
  expect(wf.activeTab).toBe('queue');
  expect(wf.activeMissionId).toBe('mission-1');
  wrapper.unmount();
});

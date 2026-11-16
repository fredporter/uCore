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

it('preserves an objective when creation fails and permits a retry', async () => {
  setActivePinia(createPinia());
  const wf = useWorkflowStore();
  const create = vi.spyOn(wf, 'createMission').mockRejectedValueOnce(new Error('Mission unavailable')).mockResolvedValueOnce();
  const wrapper = mount(MissionControlPanel);
  await wrapper.get('input').setValue('Plan a garden');
  await wrapper.get('form').trigger('submit'); await flushPromises();
  expect(wrapper.get('[role="alert"]').text()).toBe('Mission unavailable');
  expect((wrapper.get('input').element as HTMLInputElement).value).toBe('Plan a garden');
  await wrapper.get('form').trigger('submit'); await flushPromises();
  expect(create).toHaveBeenCalledTimes(2);
  expect(wrapper.find('[role="alert"]').exists()).toBe(false);
  expect((wrapper.get('input').element as HTMLInputElement).value).toBe('');
  wrapper.unmount();
});

it('shows progress and opens the active mission next task without mixing other missions', async () => {
  setActivePinia(createPinia());
  const wf = useWorkflowStore();
  wf.missions = [{ id: 'garden', title: 'Garden plan', status: 'active', priority: 'medium', description: '', taskIds: [] }];
  wf.activeMissionId = 'garden';
  const base = { priority: 'medium' as const, board: 'inbox', tags: [], description: '' };
  wf.tasks = [
    { ...base, id: 'done', title: 'Choose site', status: 'completed', mission: 'garden' },
    { ...base, id: 'next', title: 'Measure plot', status: 'in-progress', mission: 'garden' },
    { ...base, id: 'other', title: 'Unrelated work', status: 'in-progress', mission: 'other' },
  ];
  const open = vi.spyOn(wf, 'openTask').mockImplementation(() => {});
  const wrapper = mount(MissionControlPanel);
  expect(wrapper.text()).toContain('1 of 2 tasks done');
  expect(wrapper.text()).not.toContain('Unrelated work');
  await wrapper.get('.mission-control__next').trigger('click');
  expect(open).toHaveBeenCalledWith(expect.objectContaining({ id: 'next' }));
  wrapper.unmount();
});

it('does not change mission completion when its update fails', async () => {
  setActivePinia(createPinia());
  const wf = useWorkflowStore();
  wf.missions = [{ id: 'garden', title: 'Garden plan', status: 'active', priority: 'medium', description: '', taskIds: [] }];
  wf.activeMissionId = 'garden';
  vi.spyOn(wf, 'updateMission').mockRejectedValue(new Error('Save unavailable'));
  const wrapper = mount(MissionControlPanel);
  await wrapper.findAll('button').find(button => button.text() === 'Complete mission')!.trigger('click');
  await flushPromises();
  expect(wrapper.get('[role="alert"]').text()).toBe('Save unavailable');
  expect(wf.missions[0].status).toBe('active');
  wrapper.unmount();
});

// @vitest-environment jsdom
import { mount, flushPromises } from '@vue/test-utils';
import { createPinia } from 'pinia';
import { createMemoryHistory, createRouter } from 'vue-router';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import DocumentationSurface from './DocumentationSurface.vue';
import { useSettingsStore } from '../../stores/settings';
vi.mock('../../utils/diagramHydrator', () => ({hydrateDiagrams: vi.fn()}));
vi.mock('./LocalWikiReader.vue', () => ({default: {template:'<div>Knowledge library</div>'}}));
const chapters = [{name:'One',path:'01.md',source:'manual',level:'basic'}, {name:'Two',path:'02.md',source:'manual',level:'basic'}];
beforeEach(() => {
  vi.stubGlobal('localStorage', {getItem:()=>null,setItem:vi.fn(),removeItem:vi.fn()});
  vi.stubGlobal('fetch',vi.fn(async (url: string) => ({ok:true,json:async()=>url.includes('/courses') ? {courses:chapters} : {title:url.includes('02.md')?'Two':'One',content:'---\ntags: [BASIC]\n---\n# Chapter\nBody'}})));
});
async function setup(tab='learning') {
  const pinia=createPinia();
  const router=createRouter({history:createMemoryHistory(), routes:[{path:'/documentation',component:DocumentationSurface}]});
  await router.push(`/documentation?tab=${tab}`); await router.isReady();
  const wrapper=mount(DocumentationSurface,{attachTo:document.body,global:{plugins:[pinia,router]}});
  await flushPromises(); return {wrapper,pinia};
}
describe('documentation navigation',()=>{
  it('keeps chapter context when entering and exiting full-screen',async()=>{
    const {wrapper}=await setup();
    await wrapper.findAll('.learning-card')[0].trigger('click'); await flushPromises();
    expect(wrapper.get('[aria-label="Reading location"]').text()).toContain('1 of 2');
    expect(wrapper.get('[aria-label="Document properties"]').text()).toContain('BASIC');
    await wrapper.get('[aria-label="Full screen"]').trigger('click'); await flushPromises();
    expect(wrapper.find('.doc-sidepanel--fullscreen').exists()).toBe(true);
    await wrapper.get('[aria-label="Next document"]').trigger('click'); await flushPromises();
    expect(wrapper.get('[aria-label="Reading location"]').text()).toContain('2 of 2');
    expect(wrapper.get('[aria-label="Next document"]').attributes('disabled')).toBeDefined();
    document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape'})); await flushPromises();
    expect(wrapper.find('.doc-sidepanel--fullscreen').exists()).toBe(false);
    expect(wrapper.find('[aria-label="Reading view"]').exists()).toBe(true);
    await wrapper.get('[aria-label="Return to library"]').trigger('click'); await flushPromises();
    expect(wrapper.find('[aria-label="Reading view"]').exists()).toBe(false);
    wrapper.unmount();
  });
  it('hides Advanced by default and reveals it through the display preference',async()=>{
    const {wrapper,pinia}=await setup('developer');
    expect(wrapper.text()).toContain('Knowledge library');
    expect(wrapper.find('nav').text()).not.toContain('Advanced');
    useSettingsStore(pinia).setAdvancedView(true); await flushPromises();
    expect(wrapper.find('nav').text()).toContain('Advanced');
    wrapper.unmount();
  });
});

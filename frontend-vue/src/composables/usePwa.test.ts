// @vitest-environment jsdom
import { defineComponent, reactive } from 'vue';
import { mount, flushPromises } from '@vue/test-utils';
import { afterEach, expect, it, vi } from 'vitest';
import { usePwa } from './usePwa';
vi.mock('virtual:pwa-register',()=>({registerSW:vi.fn()}));
afterEach(()=>{vi.restoreAllMocks();vi.unstubAllGlobals();vi.useRealTimers();});
it('keeps local backend available when browser internet status is offline',async()=>{
 vi.spyOn(navigator,'onLine','get').mockReturnValue(false);
 vi.stubGlobal('fetch',vi.fn(async()=>({ok:true,json:async()=>({status:'ok'})})));
 const wrapper=mount(defineComponent({setup(){return {pwa:reactive(usePwa())};},template:'<div>{{pwa.online}}/{{pwa.backendAvailable}}</div>'}));
 await flushPromises();expect(wrapper.text()).toBe('false/true');wrapper.unmount();
});
it('recovers backend availability without requiring an internet status event',async()=>{
 vi.useFakeTimers();
 const request=vi.fn().mockRejectedValueOnce(new Error('unavailable')).mockResolvedValue({ok:true,json:async()=>({status:'ok'})});
 vi.stubGlobal('fetch',request);
 const wrapper=mount(defineComponent({setup(){return {pwa:reactive(usePwa())};},template:'<div>{{pwa.backendAvailable}}</div>'}));
 await flushPromises();expect(wrapper.text()).toBe('false');
 await vi.advanceTimersByTimeAsync(15000);await flushPromises();expect(wrapper.text()).toBe('true');wrapper.unmount();
});

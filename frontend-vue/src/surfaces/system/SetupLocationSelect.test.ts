// @vitest-environment jsdom
import { mount } from '@vue/test-utils';
import { expect,it } from 'vitest';
import SetupLocationSelect from './SetupLocationSelect.vue';
it('filters typed suggestions and supports keyboard selection',async()=>{
 const wrapper=mount(SetupLocationSelect,{props:{id:'city',label:'City',modelValue:'Bris',options:['Perth','Brisbane'],autocomplete:'address-level2'}});
 const input=wrapper.get('input');await input.trigger('focus');
 expect(wrapper.get('[role=listbox]').text()).toBe('Brisbane');
 await input.trigger('keydown',{key:'ArrowDown'});await input.trigger('keydown',{key:'Enter'});
 expect(wrapper.emitted('select')?.[0]).toEqual(['Brisbane']);
 expect(wrapper.find('[role=listbox]').exists()).toBe(false);wrapper.unmount();
});

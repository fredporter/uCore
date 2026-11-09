// @vitest-environment jsdom
import { mount, flushPromises } from '@vue/test-utils';
import { describe, expect, it, vi } from 'vitest';
import DocumentArticle from './DocumentArticle.vue';
vi.mock('../../utils/diagramHydrator', () => ({ hydrateDiagrams: vi.fn() }));

describe('DocumentArticle', () => {
  it('shows safe metadata pills, contents and local document navigation', async () => {
    const wrapper = mount(DocumentArticle, {props:{content:'---\ntitle: Guide\ntags: [BASIC, learning]\n---\n# Start\n## Next\n[Chapter](next.md)\n[Reference](https://example.com)'}});
    await flushPromises();
    expect(wrapper.get('[aria-label="Document properties"]').text()).toContain('BASIC');
    expect(wrapper.find('.reading-prose').text()).not.toContain('tags:');
    expect(wrapper.find('[aria-label="Document contents"]').text()).toContain('Next');
    expect(wrapper.find('a[href="https://example.com"]').exists()).toBe(false);
    await wrapper.get('a[href="next.md"]').trigger('click');
    expect(wrapper.emitted('navigate')).toEqual([['next.md']]);
    wrapper.unmount();
  });
});

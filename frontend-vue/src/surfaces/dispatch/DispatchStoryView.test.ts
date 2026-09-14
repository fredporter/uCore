// @vitest-environment jsdom

import { mount, flushPromises } from "@vue/test-utils";
import { describe, expect, it, vi, beforeEach } from "vitest";
import DispatchStoryView from "./DispatchStoryView.vue";

// Mock vue-router
vi.mock("vue-router", () => ({
  useRoute: () => ({
    params: { token: "test_token_123" },
  }),
  RouterLink: {
    template: "<a><slot /></a>",
  },
}));

describe("DispatchStoryView", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders active dispatch and supports Tri-Mode view switching", async () => {
    const fakeDispatch = {
      status: "active",
      dispatch: {
        id: "disp_100",
        token: "test_token_123",
        title: "Midsummer Solstice",
        lead_text: "A serene community celebration",
        mode_default: "card",
      },
      story_markdown: "# Welcome\n\nJoin us under the ancient oaks.\n\n---\n\n? [ ] Attend / Yes / No\n\n---\n\nThank you!",
    };

    global.fetch = vi.fn().mockResolvedValue({
      status: 200,
      json: async () => fakeDispatch,
    });

    const wrapper = mount(DispatchStoryView, {
      global: {
        stubs: {
          "router-link": { template: "<a><slot /></a>" },
        },
      },
    });
    await flushPromises();

    // Verify Title and Lead rendered
    expect(wrapper.text()).toContain("Midsummer Solstice");
    expect(wrapper.text()).toContain("A serene community celebration");

    // Starts in [Card] mode
    expect(wrapper.find(".dispatch-stage--card").exists()).toBe(true);

    // Switch to [Deck] mode
    const deckBtn = wrapper.findAll(".dispatch-mode-btn").find((b) => b.text().includes("[Deck]"));
    expect(deckBtn).toBeDefined();
    await deckBtn!.trigger("click");
    expect(wrapper.find(".dispatch-stage--deck").exists()).toBe(true);

    // Switch to [Prose] mode
    const proseBtn = wrapper.findAll(".dispatch-mode-btn").find((b) => b.text().includes("[Prose]"));
    expect(proseBtn).toBeDefined();
    await proseBtn!.trigger("click");
    expect(wrapper.find(".dispatch-stage--prose").exists()).toBe(true);
    expect(wrapper.find(".dispatch-prose-title").text()).toBe("Midsummer Solstice");
  });

  it("renders ephemeral tombstone when dispatch is burned or expired", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      status: 200,
      json: async () => ({
        status: "burned",
        tombstone: "This dispatch was ephemeral and has dissolved into the ether.",
      }),
    });

    const wrapper = mount(DispatchStoryView, {
      global: {
        stubs: {
          "router-link": { template: "<a><slot /></a>" },
        },
      },
    });
    await flushPromises();

    expect(wrapper.find(".dispatch-tombstone").exists()).toBe(true);
    expect(wrapper.text()).toContain("Ether Dissolution");
    expect(wrapper.text()).toContain("dissolved into the ether");
  });

  it("toggles calibrated aspect ratio between 16:9 and 4:3", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      status: 200,
      json: async () => ({
        status: "active",
        dispatch: { title: "Aspect Test" },
        story_markdown: "Card 1\n---\nCard 2",
      }),
    });

    const wrapper = mount(DispatchStoryView, {
      global: {
        stubs: {
          "router-link": { template: "<a><slot /></a>" },
        },
      },
    });
    await flushPromises();

    expect(wrapper.find(".aspect-16\\:9").exists()).toBe(true);

    const aspectBtn = wrapper.findAll(".dispatch-btn-sm").find((b) => b.text() === "16:9");
    expect(aspectBtn).toBeDefined();
    await aspectBtn!.trigger("click");

    expect(wrapper.find(".aspect-4\\:3").exists()).toBe(true);
  });
});

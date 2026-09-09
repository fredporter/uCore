// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import CombineResearchModal from "./CombineResearchModal.vue";

describe("CombineResearchModal", () => {
  const sources = [
    {
      path: "/vault/source-1.md",
      name: "source-1.md",
      content: "---\ntitle: Local LLMs\nsource: https://example.com/llms\n---\nLocal LLMs allow completely offline and private execution without data leakage.",
    },
    {
      path: "/vault/source-2.md",
      name: "source-2.md",
      content: "---\ntitle: Frontier Models\nsource: https://example.com/frontier\n---\nFrontier models provide higher reasoning capabilities but incur metered cloud costs.",
    },
  ];

  it("renders selected sources count and names", () => {
    const wrapper = mount(CombineResearchModal, {
      props: { sources },
      global: { stubs: { Teleport: true } },
    });

    expect(wrapper.text()).toContain("2 documents selected");
    expect(wrapper.text()).toContain("source-1.md");
    expect(wrapper.text()).toContain("source-2.md");
  });

  it("creates a synthesis document on submit", async () => {
    const wrapper = mount(CombineResearchModal, {
      props: { sources },
      global: { stubs: { Teleport: true } },
    });

    await wrapper.findAll("footer button")[1].trigger("click");

    const emitted = wrapper.emitted("create");
    expect(emitted).toHaveLength(1);
    const payload = emitted?.[0]?.[0] as { filename: string; content: string };
    expect(payload.filename).toMatch(/^research-synthesis-\d{4}-\d{2}-\d{2}\.md$/);
    expect(payload.content).toContain("type: research-synthesis");
    expect(payload.content).toContain("Local LLMs");
  });

  it("emits close on cancel", async () => {
    const wrapper = mount(CombineResearchModal, {
      props: { sources },
      global: { stubs: { Teleport: true } },
    });

    await wrapper.findAll("footer button")[0].trigger("click");
    expect(wrapper.emitted("close")).toHaveLength(1);
  });
});

// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import EnhancedBangleToolbar from "./EnhancedBangleToolbar.vue";

describe("EnhancedBangleToolbar", () => {
  it("exposes at least 25 formatting and authoring commands", () => {
    const wrapper = mount(EnhancedBangleToolbar);
    const buttons = wrapper.findAll("button.toolbar-button");
    const headings = wrapper.findAll('select[aria-label="Heading level"] option').slice(1);
    expect(buttons.length + headings.length).toBeGreaterThanOrEqual(25);
  });

  it("emits button and heading commands", async () => {
    const wrapper = mount(EnhancedBangleToolbar);
    await wrapper.get('button[aria-label^="Bold"]').trigger("click");
    await wrapper.get('select[aria-label="Heading level"]').setValue("heading-4");
    expect(wrapper.emitted("command")).toEqual([["bold"], ["heading-4"]]);
  });

  it("provides shortcut legends and labelled command groups", () => {
    const wrapper = mount(EnhancedBangleToolbar);
    expect(wrapper.get('button[aria-label^="Bold"]').attributes("title")).toContain("⌘B");
    expect(wrapper.findAll('[role="group"]').map((group) => group.attributes("aria-label"))).toContain("Research");
  });
});

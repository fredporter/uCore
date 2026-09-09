// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import AuthoringRecipeView from "./AuthoringRecipeView.vue";
import { SAMPLE_AUTHORING_WORKBENCH } from "../recipes";

describe("AuthoringRecipeView", () => {
  it("renders frontmatter metadata and document title", () => {
    const wrapper = mount(AuthoringRecipeView, {
      props: {
        recipe: SAMPLE_AUTHORING_WORKBENCH,
      },
    });

    expect(wrapper.text()).toContain("Local-First Sovereign AI Architectures");
    expect(wrapper.text()).toContain("whitepaper");
    expect(wrapper.text()).toContain("uCore Systems Team");
  });

  it("renders toolbar with Bangle formatting and research buttons", () => {
    const wrapper = mount(AuthoringRecipeView, {
      props: {
        recipe: SAMPLE_AUTHORING_WORKBENCH,
      },
    });

    const buttons = wrapper.findAll(".tb-btn");
    expect(buttons.length).toBeGreaterThanOrEqual(9);
    expect(wrapper.text()).toContain("Cite");
    expect(wrapper.text()).toContain("Combine Research");
  });

  it("renders uKnowledge citation cards and handles format switching", async () => {
    const wrapper = mount(AuthoringRecipeView, {
      props: {
        recipe: SAMPLE_AUTHORING_WORKBENCH,
      },
    });

    expect(wrapper.text()).toContain("uKnowledge Provenance");
    expect(wrapper.text()).toContain("Local-First Software: You own your data, in spite of the cloud");

    // Initially in uKnowledge callout format
    expect(wrapper.text()).toContain("> [!NOTE] Citation:");

    // Switch format to Markdown footnote
    const markdownBtn = wrapper.findAll(".format-pill-btn").find((btn) => btn.text() === "Markdown");
    expect(markdownBtn).toBeDefined();
    await markdownBtn!.trigger("click");

    expect(wrapper.text()).toContain("[^1]: [Local-First Software: You own your data, in spite of the cloud]");
  });

  it("allows switching between rendered prose and markdown source mode", async () => {
    const wrapper = mount(AuthoringRecipeView, {
      props: {
        recipe: SAMPLE_AUTHORING_WORKBENCH,
      },
    });

    // Initially in Rendered mode
    expect(wrapper.find(".prose-content").exists()).toBe(true);
    expect(wrapper.find(".markdown-textarea").exists()).toBe(false);

    // Switch to Markdown source mode
    const sourceBtn = wrapper.findAll(".mode-btn").find((btn) => btn.text().includes("Markdown Source"));
    expect(sourceBtn).toBeDefined();
    await sourceBtn!.trigger("click");

    expect(wrapper.find(".prose-content").exists()).toBe(false);
    expect(wrapper.find(".markdown-textarea").exists()).toBe(true);
  });
});

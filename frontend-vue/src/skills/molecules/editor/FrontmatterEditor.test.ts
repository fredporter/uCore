// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import FrontmatterEditor from "./FrontmatterEditor.vue";

describe("FrontmatterEditor", () => {
  it("edits visual fields and emits a validated object", async () => {
    const wrapper = mount(FrontmatterEditor, {
      props: { open: true, modelValue: { title: "Before", tags: ["one"] } },
    });
    const valueInputs = wrapper.findAll('input[aria-label$="value"]');
    await valueInputs[0].setValue("After");
    await wrapper.get(".fm-editor__save").trigger("click");

    expect(wrapper.emitted("save")?.[0]).toEqual([{ title: "After", tags: ["one"] }]);
  });

  it("blocks invalid YAML and reports the source line", async () => {
    const wrapper = mount(FrontmatterEditor, {
      props: { open: true, modelValue: { title: "Before" } },
    });
    await wrapper.findAll(".fm-editor__tabs button")[1].trigger("click");
    await wrapper.get("textarea").setValue("title: [unfinished");

    expect(wrapper.text()).toContain('Line 1: incomplete value for "title".');
    expect(wrapper.get<HTMLButtonElement>(".fm-editor__save").element.disabled).toBe(true);
    expect(wrapper.emitted("save")).toBeUndefined();
  });

  it("discards changes on cancel", async () => {
    const wrapper = mount(FrontmatterEditor, {
      props: { open: true, modelValue: { status: "draft" } },
    });
    await wrapper.findAll(".fm-editor__footer button")[0].trigger("click");
    expect(wrapper.emitted("close")).toHaveLength(1);
    expect(wrapper.emitted("save")).toBeUndefined();
  });
});

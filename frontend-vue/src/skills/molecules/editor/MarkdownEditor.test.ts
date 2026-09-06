// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";
import MarkdownEditor from "./MarkdownEditor.vue";

vi.stubGlobal("requestAnimationFrame", (callback: FrameRequestCallback) => {
  callback(0);
  return 1;
});

describe("MarkdownEditor code commands", () => {
  it("applies selection formatting through the enhanced toolbar", async () => {
    const wrapper = mount(MarkdownEditor, {
      props: { modelValue: "format me", editMode: "code" },
    });
    const textarea = wrapper.get<HTMLTextAreaElement>("textarea");
    textarea.element.setSelectionRange(0, 6);
    await wrapper.get('button[aria-label^="Bold"]').trigger("click");
    expect(wrapper.emitted("update:modelValue")?.at(-1)).toEqual(["**format** me"]);
  });

  it("inserts structural markdown and forwards governed external actions", async () => {
    const wrapper = mount(MarkdownEditor, {
      props: { modelValue: "Body", editMode: "code" },
    });
    const textarea = wrapper.get<HTMLTextAreaElement>("textarea");
    textarea.element.setSelectionRange(4, 4);
    await wrapper.get('button[aria-label="Table"]').trigger("click");
    expect(String(wrapper.emitted("update:modelValue")?.at(-1)?.[0])).toContain("| Column | Value |");
    await wrapper.get('button[aria-label="Capture research"]').trigger("click");
    expect(wrapper.emitted("toolbarAction")?.at(-1)).toEqual(["scrape"]);
  });

  it("handles platform keyboard shortcuts without submitting native input", async () => {
    const wrapper = mount(MarkdownEditor, {
      props: { modelValue: "shortcut", editMode: "code" },
    });
    const textarea = wrapper.get<HTMLTextAreaElement>("textarea");
    textarea.element.setSelectionRange(0, 8);
    await textarea.trigger("keydown", { key: "b", metaKey: true });
    expect(wrapper.emitted("update:modelValue")?.at(-1)).toEqual(["**shortcut**"]);
  });

  it("inserts validated links and switches editor mode", async () => {
    const wrapper = mount(MarkdownEditor, {
      props: { modelValue: "Docs", editMode: "code" },
      global: { stubs: { Teleport: true } },
    });
    const textarea = wrapper.get<HTMLTextAreaElement>("textarea");
    textarea.element.setSelectionRange(0, 4);
    await wrapper.get('button[aria-label^="Link"]').trigger("click");
    const inputs = wrapper.findAll("input");
    await inputs[1].setValue("https://example.com/docs");
    await wrapper.find('.markdown-insert-modal__actions button:last-child').trigger("click");
    expect(String(wrapper.emitted("update:modelValue")?.at(-1)?.[0])).toContain("[Docs](https://example.com/docs)");
    await wrapper.get('button[aria-label^="Toggle prose/code mode"]').trigger("click");
    expect(wrapper.emitted("update:editMode")?.at(-1)).toEqual(["prose"]);
  });
});

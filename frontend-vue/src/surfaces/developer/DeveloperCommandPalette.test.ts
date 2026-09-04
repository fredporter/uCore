// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import DeveloperCommandPalette from "./DeveloperCommandPalette.vue";

describe("DeveloperCommandPalette", () => {
  it("filters files and selects the highlighted result", async () => {
    const wrapper = mount(DeveloperCommandPalette, {
      props: { open: true, files: ["README.md", "src/main.ts", "src/router.ts"] },
    });
    const input = wrapper.get("input");
    await input.setValue("router");
    expect(wrapper.findAll("li")).toHaveLength(1);
    await input.trigger("keydown.enter");
    expect(wrapper.emitted("select")?.[0]).toEqual(["src/router.ts"]);
    expect(wrapper.emitted("close")).toHaveLength(1);
  });

  it("closes with Escape", async () => {
    const wrapper = mount(DeveloperCommandPalette, { props: { open: true, files: [] } });
    await wrapper.get("input").trigger("keydown.escape");
    expect(wrapper.emitted("close")).toHaveLength(1);
  });
});

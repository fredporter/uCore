// @vitest-environment jsdom

import { describe, it, expect } from "vitest"
import { mount } from "@vue/test-utils"
import BananaStudio from "./BananaStudio.vue"


describe("BananaStudio / VectorStudio", () => {
  it("renders the 5 Mono Core style presets and excludes Amber CRT", () => {
    const wrapper = mount(BananaStudio)
    expect(wrapper.text()).toContain("uVector Illustration & Asset Studio")
    expect(wrapper.text()).toContain("Ceefax Teletext")
    expect(wrapper.text()).toContain("Architectural Blueprint")
    expect(wrapper.text()).toContain("Editorial Linocut Paper")
    expect(wrapper.text()).toContain("16-Color Pixel Grid")
    expect(wrapper.text()).toContain("Technical Line Art")
    expect(wrapper.text()).not.toContain("Amber CRT Phosphor")
    expect(wrapper.text()).not.toContain("mono_amber")
  })

  it("updates selected aspect ratio on click", async () => {
    const wrapper = mount(BananaStudio)
    const aspectButtons = wrapper.findAll(".banana-studio__aspect-btn")
    expect(aspectButtons.length).toBe(5)

    await aspectButtons[1].trigger("click") // 4:3
    expect(aspectButtons[1].classes()).toContain("banana-studio__aspect-btn--active")
  })

  it("renders the studio mode tabs", () => {
    const wrapper = mount(BananaStudio)
    const modeTabs = wrapper.findAll(".banana-studio__mode-tab")
    expect(modeTabs.length).toBe(3)
    expect(wrapper.text()).toContain("Text-to-Vector")
    expect(wrapper.text()).toContain("Bitmap Tracing")
    expect(wrapper.text()).toContain("GridCore Font & Icon Map")
  })
})

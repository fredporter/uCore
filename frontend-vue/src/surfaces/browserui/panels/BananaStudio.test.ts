// @vitest-environment jsdom

import { describe, it, expect } from "vitest"
import { mount } from "@vue/test-utils"
import BananaStudio from "./BananaStudio.vue"


describe("BananaStudio", () => {
  it("renders the 4 Mono Core style presets", () => {
    const wrapper = mount(BananaStudio)
    expect(wrapper.text()).toContain("Nano Banana Asset Studio")
    expect(wrapper.text()).toContain("Ceefax Teletext")
    expect(wrapper.text()).toContain("Architectural Blueprint")
    expect(wrapper.text()).not.toContain("Amber CRT Phosphor")
    expect(wrapper.text()).toContain("Editorial Linocut Paper")
    expect(wrapper.text()).toContain("16-Color Pixel Grid")
  })

  it("updates selected aspect ratio on click", async () => {
    const wrapper = mount(BananaStudio)
    const aspectButtons = wrapper.findAll(".banana-studio__aspect-btn")
    expect(aspectButtons.length).toBe(4)

    await aspectButtons[1].trigger("click") // 16:9
    expect(aspectButtons[1].classes()).toContain("banana-studio__aspect-btn--active")
  })
})

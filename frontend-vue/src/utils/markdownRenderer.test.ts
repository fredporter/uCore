// @vitest-environment jsdom
import { describe, expect, it } from "vitest";
import { renderStory } from "./markdownRenderer";

describe("story rendering", () => {
  it("renders multi-slide markdown through Marp", async () => {
    const result = await renderStory("# One\n\n---\n\n# Two");
    expect(result.slideCount).toBe(2);
    expect(result.html).toContain("<section");
  });
});

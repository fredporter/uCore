import { describe, expect, it } from "vitest";
import { citationGenerator, detectPublicationType } from "./citationGenerator";

const source = { url: "https://docs.example.com/guide", title: "A Guide", author: "Ada", site: "Example", published: "2026-01-02", accessed: "2026-02-03" };

describe("citationGenerator", () => {
  it("detects common publication types", () => {
    expect(detectPublicationType(source.url)).toBe("documentation");
    expect(detectPublicationType("https://youtube.com/watch?v=1")).toBe("video");
  });

  it.each(["APA", "MLA", "Chicago"] as const)("formats %s citations", (format) => {
    const citation = citationGenerator(source, format);
    expect(citation).toContain("Ada");
    expect(citation).toContain("A Guide");
    expect(citation).toContain(source.url);
  });
});

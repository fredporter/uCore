import { describe, expect, it, vi } from "vitest";
import { citationGenerator, detectPublicationType, generateCitation } from "./citationGenerator";

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

  it("enriches missing titles through the governed scraper", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => ({ title: "Scraped title", url: source.url }) }));
    await expect(generateCitation({ url: source.url, author: "Ada" }, "APA")).resolves.toContain("Scraped title");
  });
});

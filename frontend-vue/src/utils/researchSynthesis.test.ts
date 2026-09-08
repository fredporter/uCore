import { describe, expect, it } from "vitest";
import { buildResearchSynthesis } from "./researchSynthesis";

const sources = [
  { path: "/research/one.md", name: "one.md", content: '---\ntitle: One\nsource: https://example.com/one\n---\nA sufficiently detailed first research claim exists here. Another useful supporting point follows this sentence.' },
  { path: "/research/two.md", name: "two.md", content: '---\ntitle: Two\n---\nA second source offers a meaningfully different claim for comparison.' },
];
describe("research synthesis", () => {
  it.each(["report", "list", "venn"] as const)("builds a %s with source links", (format) => {
    const result = buildResearchSynthesis(sources, format);
    expect(result.content).toContain("sources: [/research/one.md, /research/two.md]");
    expect(result.content).toContain("https://example.com/one");
    expect(result.content).toContain("second source");
  });
});

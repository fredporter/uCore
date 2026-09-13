// @vitest-environment jsdom
import { describe, expect, it } from "vitest";
import {
  renderStory,
  renderDocument,
  renderProseFast,
  sanitize,
} from "./markdownRenderer";

describe("markdownRenderer", () => {
  it("renders multi-slide markdown through Marp", async () => {
    const result = await renderStory("# One\n\n---\n\n# Two");
    expect(result.slideCount).toBe(2);
    expect(result.html).toContain("<section");
  });

  it("preserves SVG elements and presentation attributes through sanitize", () => {
    const rawSvg = `
      <div class="md-diagram">
        <svg viewBox="0 0 100 100" width="100" height="100">
          <circle cx="50" cy="50" r="40" fill="#00e5ff" stroke="#0b1120" stroke-width="2" />
          <path d="M 10 10 L 90 90" stroke="#ffffff" stroke-width="1" />
        </svg>
      </div>
    `;
    const cleaned = sanitize(rawSvg);
    expect(cleaned).toContain("<svg");
    expect(cleaned).toContain('viewBox="0 0 100 100"');
    expect(cleaned).toContain('cx="50"');
    expect(cleaned).toContain('cy="50"');
    expect(cleaned).toContain('r="40"');
    expect(cleaned).toContain('fill="#00e5ff"');
    expect(cleaned).toContain('stroke="#0b1120"');
    expect(cleaned).toContain('d="M 10 10 L 90 90"');
  });

  it("renders mermaid diagram code blocks into diagram containers", async () => {
    const md = "```mermaid\ngraph TD\n  A[Start] --> B[End]\n```";
    const result = await renderDocument(md);
    expect(result.html).toContain('class="md-diagram md-diagram--mermaid"');
    expect(result.html).toContain('data-diagram="mermaid"');
    expect(result.html).toContain("A[Start] --&gt; B[End]");
  });

  it("renders declarative chart code blocks directly into SVG charts", async () => {
    const md = `
\`\`\`chart
type: bar
title: Memory Usage
Chrome: 400
uCore: 80
\`\`\`
    `;
    const result = await renderDocument(md);
    expect(result.html).toContain('class="md-diagram md-diagram--chart"');
    expect(result.html).toContain('class="usx-chart usx-chart--bar"');
    expect(result.html).toContain("Memory Usage");
    expect(result.html).toContain("Chrome");
    expect(result.html).toContain("uCore");
  });

  it("renders teletext/gridcore blocks with teletext-screen pre tag", async () => {
    const md = "```teletext\n  uDos Ceefax P100\n  BBC BASIC GRID\n```";
    const result = await renderDocument(md);
    expect(result.html).toContain('class="md-diagram md-diagram--teletext"');
    expect(result.html).toContain('class="teletext-screen"');
    expect(result.html).toContain("uDos Ceefax P100");
  });

  it("renders inline and display KaTeX math formulas", async () => {
    const md = "The formula is $E = mc^2$ and block:\n\n$$\\int_0^1 x dx$$";
    const result = await renderDocument(md);
    expect(result.html).toContain("katex");
    expect(result.html).toContain("<math");
  });

  it("renders callout alert boxes correctly", () => {
    const md = "> [!NOTE]\n> Sovereign offline system";
    const html = renderProseFast(md);
    expect(html).toContain('class="md-callout md-callout--note"');
    expect(html).toContain("Sovereign offline system");
  });
});

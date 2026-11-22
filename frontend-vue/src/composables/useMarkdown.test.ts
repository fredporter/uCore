import { describe, expect, it } from "vitest";
import { renderMarkdown } from "./useMarkdown";

describe("Format Smith Markdown replies", () => {
  it("renders Markdown fences and preserves nested code", () => {
    const reply = ["````markdown", "# Notes & decisions", "```html", "<p>example</p>", "```", "````"].join("\n");
    expect(renderMarkdown(reply)).toContain("<h1>Notes &amp; decisions</h1>");
    expect(renderMarkdown(reply)).toContain("<pre><code>&lt;p&gt;example&lt;/p&gt;</code></pre>");
  });

  it("keeps ordinary and incomplete fences as escaped code", () => {
    expect(renderMarkdown("```bash\n# a comment\n```")).toBe("<pre><code># a comment</code></pre>");
    expect(renderMarkdown("```md\n<script>")).toBe("<pre><code>&lt;script&gt;</code></pre>");
  });
});

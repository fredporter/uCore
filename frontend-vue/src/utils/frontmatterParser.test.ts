import { describe, expect, it } from "vitest";
import {
  parseDocument,
  serializeDocument,
  validateYaml,
} from "./frontmatterParser";

describe("frontmatter parser", () => {
  it("round-trips supported typed frontmatter without changing the body", () => {
    const markdown = "---\ntitle: Test\ntags: [alpha, beta]\ndraft: false\nrank: 3\n---\n\n# Body\n";
    const parsed = parseDocument(markdown);

    expect(parsed.frontmatter).toEqual({
      title: "Test",
      tags: ["alpha", "beta"],
      draft: false,
      rank: 3,
    });
    expect(parseDocument(serializeDocument(parsed.body, parsed.frontmatter))).toEqual(parsed);
  });

  it("reports malformed, duplicate, and incomplete fields with line numbers", () => {
    const result = validateYaml("title: One\ninvalid line\ntitle: Two\ntags: [open");

    expect(result.errors).toEqual([
      'Line 2: expected "key: value".',
      'Line 3: duplicate field "title".',
      'Line 4: incomplete value for "tags".',
    ]);
  });
});

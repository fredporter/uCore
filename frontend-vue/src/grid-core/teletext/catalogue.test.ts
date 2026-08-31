import { describe, expect, it } from "vitest";
import {
  buildTeletextLibraries,
  normalizeLibrarySearchPayload,
  readLibrarySearchResponse,
} from "./catalogue";

describe("Teletext catalogue adapter", () => {
  it("groups valid Markdown results into the configured page ranges", () => {
    const publicDocuments = normalizeLibrarySearchPayload({
      results: [
        { path: "docs/a.md", filename: "a.md", tags: ["doc-sites"], preview: "Docs", extension: "md" },
        { path: "learn/b.md", filename: "b.md", tags: ["learning"], preview: "Learn", extension: "markdown" },
        { path: "docs/c.txt", filename: "c.txt", tags: ["doc-sites"], preview: "Text", extension: "txt" },
      ],
    });
    const knowledgeDocuments = normalizeLibrarySearchPayload({
      results: [{ path: "knowledge/d.md", filename: "d.md", tags: [], preview: "Know", extension: "md" }],
    });
    const libraries = buildTeletextLibraries(new Map([
      ["public", publicDocuments],
      ["global-knowledge", knowledgeDocuments],
    ]));

    expect(libraries.map(library => [library.id, library.page, library.docs.map(doc => doc.path)])).toEqual([
      ["documentation", 200, ["docs/a.md"]],
      ["knowledge", 300, ["knowledge/d.md"]],
      ["learning", 400, ["learn/b.md"]],
    ]);
  });

  it("rejects malformed successful and unavailable search responses", async () => {
    expect(() => normalizeLibrarySearchPayload({ results: "not-an-array" }))
      .toThrow("invalid results payload");
    await expect(readLibrarySearchResponse({ ok: false, status: 503, json: async () => ({}) }, "public"))
      .rejects.toThrow("HTTP 503 (public)");
  });
});